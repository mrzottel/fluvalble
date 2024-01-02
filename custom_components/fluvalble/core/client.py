import asyncio
import logging
import time
from typing import Callable

from bleak import BleakClient, BleakError, BLEDevice, BleakGATTCharacteristic
from bleak_retry_connector import establish_connection

from . import encryption

_LOGGER = logging.getLogger(__name__)

ACTIVE_TIME = 120
COMMAND_TIME = 15


class Client:
    def __init__(
        self,
        device: BLEDevice,
        status_callback: Callable = None,
        update_callback: Callable = None,
    ):
        self.device = device
        self.status_callback = status_callback
        self.update_callback = update_callback

        self.client: BleakClient | None = None

        self.ping_future: asyncio.Future | None = None
        self.ping_task: asyncio.Task | None = None
        self.ping_time = 0

        self.send_data = None
        self.send_time = 0
        self.connect_task = asyncio.create_task(self._connect())

        self.receive_buffer = b""

    def ping(self):
        self.ping_time = time.time() + ACTIVE_TIME

        if not self.ping_task:
            self.ping_task = asyncio.create_task(self._ping_loop())

    def notify_callback(self, sender: BleakGATTCharacteristic, data: bytearray):
        decrypted = decrypt(data)
        if len(decrypted) == 17:
            self.receive_buffer += decrypted
        else:
            _LOGGER.debug("Got all data: " + to_hex(self.receive_buffer))
            self.update_callback(self.receive_buffer)
            self.receive_buffer = b""

    async def _connect(self):
        self.client = await establish_connection(
            BleakClient, self.device, self.device.address
        )

        await self.client.start_notify(
            "00001002-0000-1000-8000-00805F9B34FB", self.notify_callback
        )

        if self.status_callback:
            self.status_callback(True)

        # Step 0
        step_zero = await self.client.read_gatt_char(
            "00001004-0000-1000-8000-00805F9B34FB"
        )

        # Step 1

        await self.client.write_gatt_char(
            "00001001-0000-1000-8000-00805F9B34FB",
            data=encrypt([0x68, 0x05]),
            response=False,
        )

    def send(self, data: bytes):
        # if send loop active - we change sending data
        self.send_time = time.time() + COMMAND_TIME
        self.send_data = data

        self.ping()

        if self.ping_future:
            self.ping_future.cancel()

    async def _ping_loop(self):
        _LOGGER.info("XXX in ping loop")
        loop = asyncio.get_event_loop()
        while time.time() < self.ping_time or True:
            try:
                _LOGGER.info("XXX in ping loop WHILE")
                self.client = await establish_connection(
                    BleakClient, self.device, self.device.address
                )
                if self.callback:
                    self.callback(True)

                # heartbeat loop
                while time.time() < self.ping_time or True:
                    # important dummy read for keep connection
                    data = await self.client.read_gatt_char(
                        "00001004-0000-1000-8000-00805F9B34FB"
                    )
                    _LOGGER.info("XXX in heartbeat loop -> " + to_hex(data))
                    if self.send_data:
                        if time.time() < self.send_time:
                            await self.client.write_gatt_char(
                                "00001002-0000-1000-8000-00805F9B34FB",
                                data=encrypt(self.send_data),
                                response=True,
                            )
                        self.send_data = None

                    # asyncio.sleep(10) with cancel
                    self.ping_future = loop.create_future()
                    loop.call_later(10, self.ping_future.cancel)
                    try:
                        await self.ping_future
                    except asyncio.CancelledError:
                        pass

                await self.client.disconnect()
            except TimeoutError:
                pass
            except BleakError as e:
                _LOGGER.debug("ping error", exc_info=e)
            except Exception as e:
                _LOGGER.warning("ping error", exc_info=e)
            finally:
                self.client = None
                if self.status_callback:
                    self.status_callback(False)
                await asyncio.sleep(1)

        self.ping_task = None


def encrypt(data: bytearray) -> bytearray:
    data = encryption.add_crc(data)
    return encryption.encrypt(data)


def decrypt(data: bytearray) -> bytearray:
    return encryption.decrypt(data)


def to_hex(data: bytes) -> str:
    return " ".join(format(x, "02x") for x in data)
