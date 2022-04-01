from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Text, BigInteger, Integer, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import os


Base = declarative_base(bind=os.getenv("POSTGRES_CONNECTION_STR"))


class ChallengeReceiptsParsed(Base):
    __tablename__ = "challenge_receipts_parsed"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    block = Column(BigInteger)
    hash = Column(Text)
    time = Column(BigInteger)
    transmitter_address = Column(Text)
    tx_power = Column(Integer)
    origin = Column(Text)
    witness_address = Column(Text)
    witness_is_valid = Column(Boolean)
    witness_invalid_reason = Column(Text)
    witness_signal = Column(Integer)
    witness_snr = Column(Float)
    witness_channel = Column(Integer)
    witness_datarate = Column(Text)
    witness_frequency = Column(Float)
    witness_timestamp = Column(BigInteger)


class PaymentsParsed(Base):
    __tablename__ = "payments_parsed"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    block = Column(BigInteger)
    hash = Column(Text)
    time = Column(BigInteger)
    payer = Column(Text)
    payee = Column(Text)
    amount = Column(BigInteger)
    type = Column(Text)
    fee = Column(BigInteger)
    nonce = Column(BigInteger)


class GatewayInventory(Base):
    __tablename__ = "gateway_inventory"

    address = Column(Text, primary_key=True, nullable=False)
    owner = Column(Text)
    location = Column(Text)
    last_poc_challenge = Column(BigInteger)
    last_poc_onion_key_hash = Column(Text)
    first_block = Column(BigInteger)
    last_block = Column(BigInteger)
    nonce = Column(BigInteger)
    name = Column(Text)
    first_timestamp = Column(BigInteger)
    reward_scale = Column(Float)
    elevation = Column(Integer)
    gain = Column(Integer)
    location_hex = Column(Text)
    mode = Column(Text)
    payer = Column(Text)


class FollowerInfo(Base):
    __tablename__ = "follower_info"

    name = Column(Text, primary_key=True)
    value = Column(BigInteger)
