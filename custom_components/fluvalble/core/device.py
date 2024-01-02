from datetime import datetime, timezone
from typing import TypedDict

from bleak import AdvertisementData, BLEDevice

from .client import Client


class Attribute(TypedDict, total=False):
    is_on: bool


class Device:
    def __init__(self, name: str, device: BLEDevice, advertisment: AdvertisementData):
        manufacturer = advertisment.manufacturer_data[171]

        self.name = name

        self.client = Client(device, self.set_connected)

        self.connected = False
        self.conn_info = {"mac": device.address}

        self.updates_connect: list = []
        self.updates_product: list = []

        self.update_ble(advertisment)

    @property
    def mac(self) -> str:
        return self.client.device.address

    def update_ble(self, advertisment: AdvertisementData):
        self.conn_info["last_seen"] = datetime.now(timezone.utc)
        self.conn_info["rssi"] = advertisment.rssi

        for handler in self.updates_connect:
            handler()

    def set_connected(self, connected: bool):
        self.connected = connected

        for handler in self.updates_connect:
            handler()

    def attribute(self, attr: str) -> Attribute:
        if attr == "connection":
            return Attribute(is_on=self.connected, extra=self.conn_info)
