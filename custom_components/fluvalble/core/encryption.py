"""Encrypts/decrypts BLE packets for the fluval LED controller."""
import logging

_LOGGER = logging.getLogger(__name__)


def encrypt(source: bytearray) -> bytearray:
    """Encrypt a BLE packet for the Fluval LED controller."""
    secret = (len(source) + 1) ^ 0x54
    header = [0x54, secret, 0x5A]
    encoded = bytearray(header)
    for b in source:
        encoded.append(b ^ 0xE)
    return encoded


def decrypt(source: bytearray | bytearray) -> bytes:
    """Decrypt a BLE packet from the Fluval LED controller."""
    key = source[0] ^ source[2]
    length = len(source)
    decrypted = bytearray()
    for i in range(3, length):
        decrypted.append(source[i] ^ key)
    return decrypted


def add_crc(source: bytearray) -> bytes:
    crc = 0x0
    for b in source:
        crc = b ^ crc
    source.append(crc)
    return source
