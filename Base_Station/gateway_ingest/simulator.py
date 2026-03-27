"""
Gateway simulator.

This mimics what a real gateway / network server would provide to the Jetson:
- dev_eui
- fcnt
- rssi/snr
- payload_raw (bytes)
- rx_time (ISO)
"""

import time
import random
from datetime import datetime, timezone

from common.payload import encode_env_payload, encode_cam_payload

class GatewaySimulator:
    def __init__(self, node_ids=range(1, 9), period_s: float = 0.25, bad_rate: float = 0.1):
        self.bad_rate = max(0.0, min(1.0, bad_rate))
        self.node_ids = list(node_ids)
        self.period_s = period_s
        self._fcnt = 0
        self._seq = 0

    def stream(self):
        while True:
            self._fcnt += 1
            node_id = random.choice(self.node_ids)

            # increment sequence number
            self._seq = (self._seq + 1) & 0xFF

            # 80% ENV packets, 20% camera events
            if random.random() < 0.8:

                payload = encode_env_payload(
                    node_id=node_id,
                    seq=self._seq,
                    temp_c=random.uniform(18, 34),
                    humidity_pct=random.uniform(20, 80),
                    battery_mv=random.randint(3600, 4200),
                    status_flags=0,
                    version=1,
                )

            else:

                payload = encode_cam_payload(
                    node_id=node_id,
                    seq=self._seq,
                    event_code=random.choice([1,2,3]),
                    people=random.randint(0,6),
                    vehicles=random.randint(0,4),
                    bikes=random.randint(0,2),
                    confidence=random.uniform(0.5,0.95),
                    dwell_s=random.randint(0,30),
                    status_flags=0,
                    version=1,
                )

            # ---- BAD PACKET INJECTION (CRC failure) ----
            if random.random() < self.bad_rate:
                b = bytearray(payload)
                b[2] ^= 0x01   # flip 1 bit (breaks CRC)
                payload = bytes(b)
            # -------------------------------------------
            
            print("SIM TX:", payload.hex())

            yield {
                "rx_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "dev_eui": "SIM_NODE",
                "fcnt": self._fcnt,
                "rssi": random.uniform(-115, -60),
                "snr": random.uniform(-5, 12),
                "payload_raw": payload,
            }

            time.sleep(self.period_s)