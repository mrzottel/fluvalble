from datetime import datetime, timezone
from typing import TypedDict, Callable

from bleak import AdvertisementData, BLEDevice

from .client import Client

NUMBERS = ["channel_1", "channel_2", "channel_3", "channel_4", "channel_5"]


class Attribute(TypedDict, total=False):
    min: int
    max: int
    step: int
    value: int

    is_on: bool


class Device:
    def __init__(self, name: str, device: BLEDevice, advertisment: AdvertisementData):
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

    def numbers(self) -> list[str]:
        return list(NUMBERS)

    def attribute(self, attr: str) -> Attribute:
        if attr == "connection":
            return Attribute(is_on=self.connected, extra=self.conn_info)

    def register_update(self, attr: str, handler: Callable):
        if attr == "connection":
            self.updates_connect.append(handler)
