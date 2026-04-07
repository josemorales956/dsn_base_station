"""
Payload encode/decode.

Supported payloads (NO LEGACY):

ENV (12 bytes total):
0: version          uint8
1: msg_type         uint8   (MSG_ENV = 0x01)
2: node_id          uint8
3: seq              uint8
4-5: temp_x100      int16 LE   (temp_c * 100)
6-7: hum_x100       uint16 LE  (humidity_pct * 100)
8-9: battery_mv     uint16 LE
10: status_flags    uint8
11: crc8            uint8      CRC over bytes [0..10]

CAM (13 bytes total):
0: version          uint8
1: msg_type         uint8   (MSG_CAM = 0x02)
2: node_id          uint8
3: seq              uint8
4: event_code       uint8   (1=periodic, 2=threshold, 3=alert)
5: people           uint8
6: vehicles         uint8
7: bikes            uint8
8: conf_x100        uint8   (0..100)
9-10: dwell_s       uint16 LE
11: status_flags    uint8
12: crc8            uint8      CRC over bytes [0..11]

SNAPSHOT (19 bytes total):
0: version          uint8
1: msg_type         uint8   (MSG_SNAPSHOT = 0x03)
2: node_id          uint8
3: seq              uint8
4-5: temp_x100      int16 LE   (temp_c * 100)
6-7: hum_x100       uint16 LE  (humidity_pct * 100)
8-9: battery_mv     uint16 LE
10: event_code      uint8
11: people          uint8
12: vehicles        uint8
13: bikes           uint8
14: conf_x100       uint8   (0..100)
15-16: dwell_s      uint16 LE
17: status_flags    uint8
18: crc8            uint8      CRC over bytes [0..17]
"""

import struct
from common.crc8 import crc8

# Message types
MSG_ENV = 0x01
MSG_CAM = 0x02
MSG_SNAPSHOT = 0x03

# Payload lengths
ENV_LEN = 12
CAM_LEN = 13
SNAPSHOT_LEN = 19


# -------------------
# Encoders
# -------------------

def encode_env_payload(
    node_id: int,
    seq: int,
    temp_c: float,
    humidity_pct: float,
    battery_mv: int,
    status_flags: int = 0,
    version: int = 1,
) -> bytes:
    temp_x100 = int(round(temp_c * 100))
    hum_x100 = int(round(humidity_pct * 100))

    base = struct.pack(
        "<BBBBhHHB",
        version & 0xFF,
        MSG_ENV,
        node_id & 0xFF,
        seq & 0xFF,
        temp_x100,
        hum_x100 & 0xFFFF,
        battery_mv & 0xFFFF,
        status_flags & 0xFF,
    )
    return base + bytes([crc8(base)])


def encode_cam_payload(
    node_id: int,
    seq: int,
    event_code: int,
    people: int,
    vehicles: int,
    bikes: int = 0,
    confidence: float = 0.0,
    dwell_s: int = 0,
    status_flags: int = 0,
    version: int = 1,
) -> bytes:
    conf_x100 = int(round(confidence * 100))
    conf_x100 = 0 if conf_x100 < 0 else 100 if conf_x100 > 100 else conf_x100

    base = struct.pack(
        "<BBBBBBBBBHB",
        version & 0xFF,
        MSG_CAM,
        node_id & 0xFF,
        seq & 0xFF,
        event_code & 0xFF,
        people & 0xFF,
        vehicles & 0xFF,
        bikes & 0xFF,
        conf_x100 & 0xFF,
        dwell_s & 0xFFFF,
        status_flags & 0xFF,
    )
    return base + bytes([crc8(base)])


def encode_snapshot_payload(
    node_id: int,
    seq: int,
    temp_c: float,
    humidity_pct: float,
    battery_mv: int,
    event_code: int,
    people: int,
    vehicles: int,
    bikes: int = 0,
    confidence: float = 0.0,
    dwell_s: int = 0,
    status_flags: int = 0,
    version: int = 1,
) -> bytes:
    temp_x100 = int(round(temp_c * 100))
    hum_x100 = int(round(humidity_pct * 100))

    conf_x100 = int(round(confidence * 100))
    conf_x100 = 0 if conf_x100 < 0 else 100 if conf_x100 > 100 else conf_x100

    base = struct.pack(
        "<BBBBhHHBBBBBHB",
        version & 0xFF,
        MSG_SNAPSHOT,
        node_id & 0xFF,
        seq & 0xFF,
        temp_x100,
        hum_x100 & 0xFFFF,
        battery_mv & 0xFFFF,
        event_code & 0xFF,
        people & 0xFF,
        vehicles & 0xFF,
        bikes & 0xFF,
        conf_x100 & 0xFF,
        dwell_s & 0xFFFF,
        status_flags & 0xFF,
    )
    return base + bytes([crc8(base)])


# -------------------
# Decoder
# -------------------

def decode_payload(raw: bytes) -> dict:
    if not isinstance(raw, (bytes, bytearray)):
        raise TypeError("payload must be bytes")
    raw = bytes(raw)
    n = len(raw)

    # ENV (12B)
    if n == ENV_LEN:
        base, got_crc = raw[:-1], raw[-1]
        want_crc = crc8(base)
        if got_crc != want_crc:
            raise ValueError(f"CRC mismatch: got 0x{got_crc:02X}, want 0x{want_crc:02X}")

        version, msg_type, node_id, seq, temp_x100, hum_x100, batt_mv, flags = struct.unpack("<BBBBBhHHB", base)
        if msg_type != MSG_ENV:
            raise ValueError(f"Unexpected msg_type for ENV_LEN: 0x{msg_type:02X}")

        return {
            "payload_version": int(version),
            "msg_type": "ENV",
            "msg_type_id": int(msg_type),
            "node_id": int(node_id),
            "seq": int(seq),
            "temp_c": temp_x100 / 100.0,
            "humidity_pct": hum_x100 / 100.0,
            "battery_mv": int(batt_mv),
            "status_flags": int(flags),
        }

    # CAM (13B)
    if n == CAM_LEN:
        base, got_crc = raw[:-1], raw[-1]
        want_crc = crc8(base)
        if got_crc != want_crc:
            raise ValueError(f"CRC mismatch: got 0x{got_crc:02X}, want 0x{want_crc:02X}")

        (
            version, msg_type, node_id, seq,
            event_code, people, vehicles, bikes,
            conf_x100, dwell_s, flags
        ) = struct.unpack("<BBBBBBBBBHB", base)

        if msg_type != MSG_CAM:
            raise ValueError(f"Unexpected msg_type for CAM_LEN: 0x{msg_type:02X}")

        return {
            "payload_version": int(version),
            "msg_type": "CAM",
            "msg_type_id": int(msg_type),
            "node_id": int(node_id),
            "seq": int(seq),
            "event_code": int(event_code),
            "people": int(people),
            "vehicles": int(vehicles),
            "bikes": int(bikes),
            "mean_conf": float(conf_x100) / 100.0,
            "dwell_s": int(dwell_s),
            "status_flags": int(flags),
        }

    # SNAPSHOT (19B)
    if n == SNAPSHOT_LEN:
        base, got_crc = raw[:-1], raw[-1]
        want_crc = crc8(base)
        if got_crc != want_crc:
            raise ValueError(f"CRC mismatch: got 0x{got_crc:02X}, want 0x{want_crc:02X}")

        (
            version, msg_type, node_id, seq,
            temp_x100, hum_x100, batt_mv,
            event_code, people, vehicles, bikes,
            conf_x100, dwell_s, flags
        ) = struct.unpack("<BBBBhHHBBBBBHB", base)

        if msg_type != MSG_SNAPSHOT:
            raise ValueError(f"Unexpected msg_type for SNAPSHOT_LEN: 0x{msg_type:02X}")

        return {
            "payload_version": int(version),
            "msg_type": "SNAPSHOT",
            "msg_type_id": int(msg_type),
            "node_id": int(node_id),
            "seq": int(seq),
            "temp_c": temp_x100 / 100.0,
            "humidity_pct": hum_x100 / 100.0,
            "battery_mv": int(batt_mv),
            "event_code": int(event_code),
            "people": int(people),
            "vehicles": int(vehicles),
            "bikes": int(bikes),
            "mean_conf": float(conf_x100) / 100.0,
            "dwell_s": int(dwell_s),
            "status_flags": int(flags),
        }

    raise ValueError(f"Bad payload length: {n} (expected {ENV_LEN}, {CAM_LEN}, or {SNAPSHOT_LEN})")