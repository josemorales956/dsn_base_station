"""
Payload encode/decode.

Payload format (10 bytes total):
0: version          uint8
1: node_id          uint8
2-3: temp_x100       int16 LE   (temp_c * 100)
4-5: hum_x100        uint16 LE  (humidity_pct * 100)
6-7: battery_mv      uint16 LE
8: status_flags      uint8
9: crc8              uint8      CRC over bytes [0..8]
"""

import struct
from common.crc8 import crc8

PAYLOAD_LEN = 10

def encode_payload(
    node_id: int,
    temp_c: float,
    humidity_pct: float,
    battery_mv: int,
    status_flags: int = 0,
    version: int = 1,
) -> bytes:
    temp_x100 = int(round(temp_c * 100))
    hum_x100 = int(round(humidity_pct * 100))

    base = struct.pack(
        "<BBhHHB",
        version & 0xFF,
        node_id & 0xFF,
        temp_x100,
        hum_x100 & 0xFFFF,
        battery_mv & 0xFFFF,
        status_flags & 0xFF,
    )

    return base + bytes([crc8(base)])

def decode_payload(raw: bytes) -> dict:
    if len(raw) != PAYLOAD_LEN:
        raise ValueError(f"Bad payload length: {len(raw)} (expected {PAYLOAD_LEN})")

    base, got_crc = raw[:-1], raw[-1]
    want_crc = crc8(base)
    if got_crc != want_crc:
        raise ValueError(f"CRC mismatch: got 0x{got_crc:02X}, want 0x{want_crc:02X}")

    version, node_id, temp_x100, hum_x100, batt_mv, flags = struct.unpack("<BBhHHB", base)

    return {
        "payload_version": int(version),
        "node_id": int(node_id),
        "temp_c": temp_x100 / 100.0,
        "humidity_pct": hum_x100 / 100.0,
        "battery_mv": int(batt_mv),
        "status_flags": int(flags),
    }