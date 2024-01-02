"""Encrypts/decrypts BLE packets for the fluval LED controller."""

def encrypt(source: bytes | bytearray) -> bytes:
    """Encrypt a BLE packet for the Fluval LED controller."""
    for b in source:
        b = b ^ 0xE
    secret = (len(source) + 1) ^ 0x54
    header = [0x54, secret, 0x5A]
    encoded = header + source
    return encoded


def decrypt(source: bytes | bytearray) -> bytes:
    """Decrypt a BLE packet from the Fluval LED controller."""
    key = source[0] ^ source[2]
    length = len(source)
    decrypted = b""
    for i in range(3, length):
        decrypted += source[i] ^ key
    return decrypted
