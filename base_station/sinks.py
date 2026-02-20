"""
Sinks decide where the base station sends normalized records.
For now: stdout JSON (easy for DB teammate to ingest).
"""

import json
from pathlib import Path
from datetime import datetime

class StdoutJsonSink:
    def write(self, record: dict) -> None:
        print(json.dumps(record))


class JsonlFileSink:
    """
    Writes each valid uplink as a JSON line.
    """
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


class ErrorLogSink:
    """
    Logs bad packet errors to a file.
    """
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, message: str) -> None:
        timestamp = datetime.utcnow().isoformat()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")