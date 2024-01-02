"""Client class connecting the Fluval BLE Entity to a bluetooth connection."""

import asyncio
from collections.abc import Callable
import contextlib
import logging
import time

from bleak import BleakClient, BleakError, BleakGATTCharacteristic, BLEDevice
from bleak_retry_connector import establish_connection

from . import encryption

_LOGGER = logging.getLogger(__name__)

ACTIVE_TIME = 120
COMMAND_TIME = 15


class Client:
    """Basic client handling BLE sending and callbacks."""

    def __init__(
        self,
        device: BLEDevice,
        status_callback: Callable = None,
        update_callback: Callable = None,
    ) -> None:
        """Initialize the client."""
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
        """Start the ping task to periodically talk to the Fluval."""
        self.ping_time = time.time() + ACTIVE_TIME

        if not self.ping_task:
            self.ping_task = asyncio.create_task(self._ping_loop())

    def notify_callback(self, sender: BleakGATTCharacteristic, data: bytearray):
        """Handle packets sent by the Fluval."""
        decrypted = decrypt(data)
        if len(decrypted) == 17:
            self.receive_buffer += decrypted
        else:
            _LOGGER.debug("Got all data: %s ", to_hex(self.receive_buffer))
            self.update_callback(self.receive_buffer)
            self.receive_buffer = b""

    async def _connect(self):
        """Connect to the Fluval and subscribe to notifications."""
        self.client = await establish_connection(
            BleakClient, self.device, self.device.address
        )

        await self.client.start_notify(
            "00001002-0000-1000-8000-00805F9B34FB", self.notify_callback
        )

        if self.status_callback:
            self.status_callback(True)

        # Step 0
        await self.client.read_gatt_char("00001004-0000-1000-8000-00805F9B34FB")

        # Step 1

        await self.client.write_gatt_char(
            "00001001-0000-1000-8000-00805F9B34FB",
            data=encrypt([0x68, 0x05]),
            response=False,
        )

    def send(self, data: bytes):
        """Send a packet to the Fluval."""
        # if send loop active - we change sending data
        self.send_time = time.time() + COMMAND_TIME
        self.send_data = data

        self.ping()

        if self.ping_future:
            self.ping_future.cancel()

    async def _ping_loop(self):
        """Ping the Fluval to keep connection."""
        # TODO: Set current time instead of dummy packet
        loop = asyncio.get_event_loop()
        while time.time() < self.ping_time or True:
            try:
                self.client = await establish_connection(
                    BleakClient, self.device, self.device.address
                )
                if self.callback:
                    self.callback(True)

                # heartbeat loop
                while time.time() < self.ping_time or True:
                    # important dummy read for keep connection
                    await self.client.read_gatt_char(
                        "00001004-0000-1000-8000-00805F9B34FB"
                    )
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
                    with contextlib.suppress(asyncio.CancelledError):
                        await self.ping_future

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
    """Encrypt a packet for sending to Fluval."""
    data = encryption.add_crc(data)
    return encryption.encrypt(data)


def decrypt(data: bytearray) -> bytearray:
    """Decrypt a packet that has been received by the Fluval."""
    return encryption.decrypt(data)


def to_hex(data: bytes) -> str:
    """Print a byte array as hex strings for debugging."""
    return " ".join(format(x, "02x") for x in data)
