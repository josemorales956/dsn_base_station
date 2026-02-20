"""
CRC-8 (poly 0x07) utility.

This is used to validate payload integrity.
Keep this identical across node + base station.
"""

POLY = 0x07  # CRC-8-ATM

def crc8(data: bytes, init: int = 0x00) -> int:
    crc = init & 0xFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ POLY) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc