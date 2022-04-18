from dotenv import load_dotenv
import os
from distutils.util import strtobool


class Settings(object):
    def __init__(self):
        load_dotenv()
        self._node_address = os.getenv('NODE_ADDRESS')
        self._postgres_connection_string = os.getenv('POSTGRES_CONNECTION_STR')

        self._gateway_inventory_bootstrap: bool = strtobool(os.getenv('GATEWAY_INVENTORY_BOOTSTRAP'))
        self._gateway_inventory_path = os.getenv('GATEWAY_INVENTORY_PATH')

        self._denylist_url = os.getenv('DENYLIST_URL')
        self._denylist_bootstrap: bool = strtobool(os.getenv('DENYLIST_BOOTSTRAP'))

        self._block_inventory_size = os.getenv('BLOCK_INVENTORY_SIZE')
        self._logs_path = os.getenv('LOGS_PATH')
        self._latest_inventories_url = os.getenv('LATEST_INVENTORIES_URL')

    @property
    def node_address(self):
        return self._node_address

    @property
    def postgres_connection_string(self):
        return self._postgres_connection_string

    @property
    def gateway_inventory_bootstrap(self):
        return self._gateway_inventory_bootstrap

    @property
    def gateway_inventory_path(self):
        return self._gateway_inventory_path

    @property
    def block_inventory_size(self):
        return int(self._block_inventory_size)

    @property
    def logs_path(self):
        return os.getenv('LOGS_PATH')

    @property
    def latest_inventories_url(self):
        return self._latest_inventories_url

    @property
    def denylist_url(self):
        return self._denylist_url

    @property
    def denylist_bootstrap(self):
        return self._denylist_bootstrap

