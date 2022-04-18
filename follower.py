import pandas as pd
import psycopg2.errors
import sqlalchemy.exc

from models.block import *
from models.transactions.poc_receipts_v1 import *
from models.transactions.payment_v2 import *
from models.transactions.payment_v1 import *
from models.transactions.state_channel_close_v1 import *
from models.migrations import *
from client import BlockchainNodeClient
from loaders import *
from settings import Settings
from constants import *

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from geoalchemy2 import func
import h3
from haversine import haversine, Unit

import time
import hashlib
import json
from pydantic.error_wrappers import ValidationError


class Follower(object):
    def __init__(self):
        self.settings = Settings()

        self.client = BlockchainNodeClient(self.settings)

        self.engine = create_engine(self.settings.postgres_connection_string)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.height = self.client.height
        self.first_block: Optional[int] = None
        self.sync_height: Optional[int] = None
        self.inventory_height: Optional[int] = None
        self.denylist_tag: Optional[int] = None

        self.gateway_locations: Optional[pd.DataFrame] = None

    def run(self):
        if self.settings.gateway_inventory_bootstrap:
            self.update_gateway_inventory()
            print("Gateway inventory imported successfully")

        if self.settings.denylist_bootstrap:
            self.update_denylist()
            print("Denylist imported successfully")

        try:
            self.get_follower_info()
        except sqlalchemy.exc.NoResultFound:
            pass

        self.gateway_locations = pd.read_sql("SELECT address, location FROM gateway_inventory;", con=self.engine, index_col="address")
        self.gateway_locations["coordinates"] = self.gateway_locations["location"].map(h3.h3_to_geo)

        self.get_first_block()
        self.update_follower_info()

        print(f"Blockchain follower starting from block {self.sync_height} / {self.height}")

        while True:
            t = time.time()

            retry = 0

            while retry < 50:
                try:
                    if (self.sync_height - self.inventory_height > 500) and (self.sync_height % 100 == 0):
                        print("Checking for new dump of gateway_inventory")
                        available_height = get_latest_inventory_height(self.settings)
                        if available_height > self.inventory_height:
                            print("Found one!")
                            self.update_gateway_inventory()
                        else:
                            print("No new version found.")

                        print("Checking for new release of denylist")
                        latest_tag = int(get_latest_denylist_tag())
                        if latest_tag != self.denylist_tag:
                            print("Found one!")
                            self.update_denylist()
                        else:
                            print("No new version found.")

                    self.process_block(self.sync_height)
                    self.delete_old_receipts()
                    break
                except (ValidationError, AttributeError):
                    print("couldn't find transaction...retrying")
                    time.sleep(10)
                    retry += 1
            self.sync_height += 1

            print(f"Block {self.sync_height - 1} synced in {time.time() - t} seconds...")
            self.update_follower_info()
            if self.sync_height >= self.height:
                time.sleep(10)

    def get_follower_info(self):
        self.sync_height = self.session.query(FollowerInfo.value).filter(FollowerInfo.name == "sync_height").one()[0]
        self.first_block = self.session.query(FollowerInfo.value).filter(FollowerInfo.name == "first_block").one()[0]
        self.inventory_height = self.session.query(FollowerInfo.value).filter(FollowerInfo.name == "inventory_height").one()[0]
        self.denylist_tag = self.session.query(FollowerInfo.value).filter(FollowerInfo.name == "denylist_tag").one()[0]

    def get_first_block(self):
        print("Getting first block...")
        if self.first_block:
            print(f"first_block height found from database: {self.first_block}")
        else:
            h = self.height
            while True:
                if h < (self.height - self.settings.block_inventory_size) or self.client.block_get(h, None) is None:
                    self.first_block = h + 1
                    print(f"first_block height found!: {self.first_block}")
                    break
                else:
                    h -= 1
                    if h % 100 == 0:
                        print(f"...still finding blocks, at {h} / {self.height}")

    def update_follower_info(self):
        if not self.first_block:
            self.get_first_block()
        if not self.sync_height:
            self.sync_height = self.first_block
        if not self.inventory_height:
            self.update_gateway_inventory()
        follower_info = [
            FollowerInfo(name="height", value=self.height),
            FollowerInfo(name="first_block", value=self.first_block),
            FollowerInfo(name="sync_height", value=self.sync_height),
            FollowerInfo(name="inventory_height", value=self.inventory_height),
            FollowerInfo(name="denylist_tag", value=self.denylist_tag)
        ]

        try:
            self.session.add_all(follower_info)
            self.session.commit()

        except sqlalchemy.exc.IntegrityError:
            self.session.rollback()
            for row in follower_info:
                self.session.query(FollowerInfo).filter(FollowerInfo.name == row.name).\
                    update({"value": row.value})

        self.session.commit()

    def update_gateway_inventory(self):
        print("Updating gateway_inventory...")
        gateway_inventory, inventory_height = process_gateway_inventory(self.settings)
        gateway_inventory["address"] = gateway_inventory.index
        # replace instead of delete + append
        # try:
        #     self.session.query(GatewayInventory).delete()
        #     self.session.commit()
        # except sqlalchemy.exc.IntegrityError:
        #     self.session.rollback()
        # gateway_inventory.to_sql("gateway_inventory", con=self.engine, if_exists="replace")
        gateway_rows = gateway_inventory.to_dict("index")

        entries_to_update, entries_to_put = [], []
        # Find all customers that needs to be updated and build mappings
        for each in (
                self.session.query(GatewayInventory.address).filter(GatewayInventory.address.in_(gateway_rows.keys())).all()
        ):
            gateway = gateway_rows.pop(each.address)
            entries_to_update.append(gateway)

        # Bulk mappings for everything that needs to be inserted
        entries_to_put = [v for v in gateway_rows.values()]

        self.session.bulk_insert_mappings(GatewayInventory, entries_to_put)
        self.session.bulk_update_mappings(GatewayInventory, entries_to_update)
        self.session.commit()

        self.inventory_height = inventory_height
        print(f"Done. Inventory up to date as of block {self.inventory_height}")

    def update_denylist(self):
        print("Updating denylist...")
        denylist = get_denylist(self.settings)
        try:
            self.session.query(Denylist).delete()
            self.session.commit()
        except sqlalchemy.exc.IntegrityError:
            self.session.rollback()
        denylist.to_sql("denylist", con=self.engine, if_exists="append")
        self.denylist_tag = int(get_latest_denylist_tag())
        print(f"Done. Denylist up to date as of tag {self.denylist_tag}")


    def process_block(self, height: int):
        block = self.client.block_get(height, None)
        parsed_receipts = []
        parsed_payments = []
        parsed_summaries = []
        _t = time.time()

        for txn in block.transactions:
            if txn.type == "payment_v1":
                transaction: PaymentV1 = self.client.transaction_get(txn.hash, txn.type)
                parsed_payment = PaymentsParsed(
                    block=height,
                    hash=txn.hash,
                    amount=transaction.amount,
                    type=txn.type,
                    fee=transaction.fee,
                    nonce=transaction.nonce,
                    time=block.time,
                    payer=transaction.payer,
                    payee=transaction.payee
                )
                parsed_payments.append(parsed_payment)

            elif txn.type == "payment_v2":
                transaction: PaymentV2 = self.client.transaction_get(txn.hash, txn.type)
                for payment in transaction.payments:
                    parsed_payment = PaymentsParsed(
                        block=height,
                        hash=txn.hash,
                        amount=payment.amount,
                        type=txn.type,
                        fee=transaction.fee,
                        nonce=transaction.nonce,
                        time=block.time,
                        payer=transaction.payer,
                        payee=payment.payee
                    )
                    parsed_payments.append(parsed_payment)

            if txn.type == "poc_receipts_v1":
                transaction: PocReceiptsV1 = self.client.transaction_get(txn.hash, txn.type)
                if not self.session.query(GatewayInventory.address).where(GatewayInventory.address == transaction.path[0].challengee).first():
                    continue
                for witness in transaction.path[0].witnesses:
                    if not self.session.query(GatewayInventory.address).where(GatewayInventory.address == witness.gateway).first():
                        continue
                    parsed_receipt = ChallengeReceiptsParsed(
                        block=block.height,
                        hash=txn.hash,
                        time=block.time,
                        challenger=transaction.challenger,
                        transmitter_address=transaction.path[0].challengee,
                        witness_address=witness.gateway,
                        witness_is_valid=witness.is_valid,
                        witness_invalid_reason=witness.invalid_reason,
                        witness_signal=witness.signal,
                        witness_snr=witness.snr,
                        witness_channel=witness.channel,
                        witness_datarate=witness.datarate,
                        witness_frequency=witness.frequency,
                        witness_timestamp=witness.timestamp,
                        distance_km=self.get_distance_between_gateways(transaction.path[0].challengee, witness.gateway)
                    )

                    if transaction.path[0].receipt:
                        parsed_receipt.tx_power = transaction.path[0].receipt.tx_power
                        parsed_receipt.origin = transaction.path[0].receipt.origin
                    parsed_receipts.append(parsed_receipt)
            elif txn.type == "state_channel_close_v1":
                transaction: StateChannelCloseV1 = self.client.transaction_get(txn.hash, txn.type)
                for summary in transaction.state_channel.summaries:
                    if not self.session.query(GatewayInventory.address).where(GatewayInventory.address == summary.client).first():
                        continue
                    parsed_summary = DataCredits(
                        block=transaction.block,
                        hash=txn.hash,
                        client=summary.client,
                        num_dcs=summary.num_dcs,
                        num_packets=summary.num_packets
                    )
                    parsed_summaries.append(parsed_summary)

        self.session.add_all(parsed_receipts)
        self.session.add_all(parsed_payments)
        self.session.add_all(parsed_summaries)
        self.session.commit()

    def delete_old_receipts(self):
        self.session.query(ChallengeReceiptsParsed).filter(ChallengeReceiptsParsed.block < (self.sync_height - self.settings.block_inventory_size)).delete()
        self.session.query(DataCredits).filter(DataCredits.block < (self.sync_height - self.settings.block_inventory_size)).delete()
        self.session.query(PaymentsParsed).filter(PaymentsParsed.block < (self.sync_height - self.settings.block_inventory_size)).delete()
        self.session.commit()

    def get_distance_between_gateways(self, tx_address, rx_address):
        try:
            return haversine(self.gateway_locations["coordinates"][tx_address],
                             self.gateway_locations["coordinates"][rx_address],
                             unit=Unit.KILOMETERS)
        except KeyError:
            return None


def get_hash_of_dict(d: dict) -> str:
    return hashlib.md5(json.dumps(d, sort_keys=True).encode('utf-8')).hexdigest()


