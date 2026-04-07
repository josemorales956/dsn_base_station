from common.payload import encode_snapshot_payload

payload = encode_snapshot_payload(
    node_id=3,
    seq=1,
    temp_c=25.50,
    humidity_pct=60.00,
    battery_mv=3700,
    event_code=1,
    people=2,
    vehicles=3,
    bikes=6,
    confidence=0.87,
    dwell_s=15,
    status_flags=0,
    version=1,
)

print(payload.hex().upper())