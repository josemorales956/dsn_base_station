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

from common.payload import encode_payload

class GatewaySimulator:
    def __init__(self, node_ids=(1, 2, 3), period_s: float = 2.0, bad_rate: float = 0.2):
        self.bad_rate = max(0.0, min(1.0, bad_rate))
        self.node_ids = list(node_ids)
        self.period_s = period_s
        self._fcnt = 0

    def stream(self):
        while True:
            self._fcnt += 1
            node_id = random.choice(self.node_ids)

            payload = encode_payload(
                node_id=node_id,
                temp_c=random.uniform(18, 34),
                humidity_pct=random.uniform(20, 80),
                battery_mv=random.randint(3600, 4200),
                status_flags=0,
                version=1,
            )
            # ---- BAD PACKET INJECTION (CRC failure) ----
            if random.random() < self.bad_rate:
                b = bytearray(payload)
                b[2] ^= 0x01   # flip 1 bit (breaks CRC)
                payload = bytes(b)
            # -------------------------------------------
            yield {
                "rx_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "dev_eui": "SIM_NODE",
                "fcnt": self._fcnt,
                "rssi": random.uniform(-115, -60),
                "snr": random.uniform(-5, 12),
                "payload_raw": payload,
            }

            time.sleep(self.period_s)