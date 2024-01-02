from datetime import datetime, timezone
from typing import TypedDict, Callable

import logging

from bleak import AdvertisementData, BLEDevice

from .client import Client

_LOGGER = logging.getLogger(__name__)

NUMBERS = ["channel_1", "channel_2", "channel_3", "channel_4", "channel_5"]
SELECTS = ["mode"]
MODES = ["manual", "automatic", "professional"]


class Attribute(TypedDict, total=False):
    options: list[str]
    default: str

    min: int
    max: int
    step: int
    value: int

    is_on: bool
    extra: dict


class Device:
    def __init__(self, name: str, device: BLEDevice, advertisment: AdvertisementData):
        self.name = name
        self.client = Client(device, self.set_connected, self.decode_update_packet)
        self.connected = False
        self.conn_info = {"mac": device.address}
        self.updates_connect: list = []
        self.updates_component: list = []
        self.channel_1 = 0
        self.channel_2 = 0
        self.channel_3 = 0
        self.channel_4 = 0
        self.channel_5 = 0
        self.mode = ""
        self.led_on = False
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

    def selects(self) -> list[str]:
        return list(SELECTS)

    def attribute(self, attr: str) -> Attribute:
        _LOGGER.debug("XXX -> attr: " + attr)
        if attr == "connection":
            return Attribute(is_on=self.connected, extra=self.conn_info)
        if attr == "channel_1":
            return Attribute(min=0, max=1000, step=50, value=self.channel_1)
        if attr == "channel_2":
            return Attribute(min=0, max=1000, step=50, value=self.channel_2)
        if attr == "channel_3":
            return Attribute(min=0, max=1000, step=50, value=self.channel_3)
        if attr == "channel_4":
            return Attribute(min=0, max=1000, step=50, value=self.channel_4)
        if attr == "channel_5":
            return Attribute(min=0, max=1000, step=50, value=self.channel_5)
        if attr == "mode":
            return Attribute(options=MODES, default=self.mode)

    def register_update(self, attr: str, handler: Callable):
        if attr == "connection":
            self.updates_connect.append(handler)
        else:
            self.updates_component.append(handler)

    def decode_update_packet(self, data: bytearray):
        if data[2] == 0x00:
            self.mode = MODES[0]
        elif data[2] == 0x01:
            self.mode = MODES[1]
        elif data[2] == 0x02:
            self.mode = MODES[2]

        self.led_on = data[3] > 0x00
        if self.mode == "manual":
            self.channel_1 = (data[6] << 8) | (data[5] & 0xFF)
            self.channel_2 = (data[8] << 8) | (data[7] & 0xFF)
            self.channel_3 = (data[10] << 8) | (data[9] & 0xFF)
            self.channel_4 = (data[12] << 8) | (data[11] & 0xFF)
        else:
            self.channel_1 = 0
            self.channel_2 = 0
            self.channel_3 = 0
            self.channel_4 = 0

        _LOGGER.debug(
            "led: "
            + str(self.led_on)
            + " mode: "
            + str(self.mode)
            + " channels: "
            + str(self.channel_1)
            + " / "
            + str(self.channel_2)
            + " / "
            + str(self.channel_3)
            + " / "
            + str(self.channel_4)
        )

        for handler in self.updates_component:
            handler()
