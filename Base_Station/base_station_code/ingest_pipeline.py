"""
Base station ingest pipeline.

Takes a normalized uplink message and returns a normalized record:
metadata + decoded payload fields.
"""

from common.payload import decode_payload

def process_uplink(uplink: dict):
    try:
        decoded = decode_payload(uplink["payload_raw"])
    except Exception as e:
        return None, f"Decode failed for fcnt={uplink.get('fcnt')}: {e}"

    record = {
        "rx_time": uplink["rx_time"],
        "dev_eui": uplink["dev_eui"],
        "fcnt": uplink["fcnt"],
        "rssi": uplink["rssi"],
        "snr": uplink["snr"],
        **decoded,
    }

    return record, None