from common.payload import encode_snapshot_payload

payload = encode_snapshot_payload(
    node_id=1,
    seq=1,
    temp_c=25.34,
    humidity_pct=61.27,
    battery_mv=3720,
    event_code=1,
    people=4,
    vehicles=2,
    bikes=1,
    confidence=0.87,
    dwell_s=12,
    status_flags=0,
    version=1,
)

print(payload.hex().upper())