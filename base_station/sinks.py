"""
Sinks decide where the base station sends normalized records.
For now: stdout JSON (easy for DB teammate to ingest).
"""

import time
import json
import sqlite3
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


class SqliteSink:
    """
    Stores normalized uplink records into SQLite.
    Also stores decode/processing errors into bad_packets (same DB connection).
    """

    SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS uplinks (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,

      rx_time         TEXT    NOT NULL,
      dev_eui         TEXT    NOT NULL,
      fcnt            INTEGER NOT NULL,

      rssi            REAL,
      snr             REAL,

      payload_version INTEGER,
      node_id         INTEGER,
      temp_c          REAL,
      humidity_pct    REAL,
      battery_mv      INTEGER,
      status_flags    INTEGER,

      record_json     TEXT,

      UNIQUE(dev_eui, fcnt)
    );

    CREATE INDEX IF NOT EXISTS idx_uplinks_time
      ON uplinks(rx_time);

    CREATE INDEX IF NOT EXISTS idx_uplinks_node_time
      ON uplinks(node_id, rx_time);

    CREATE TABLE IF NOT EXISTS bad_packets (
      id               INTEGER PRIMARY KEY AUTOINCREMENT,
      rx_time          TEXT,
      dev_eui          TEXT,
      fcnt             INTEGER,
      error            TEXT    NOT NULL,
      received_at_unix INTEGER NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_bad_packets_received
      ON bad_packets(received_at_unix);
    """

    INSERT_SQL = """
    INSERT INTO uplinks (
      rx_time, dev_eui, fcnt, rssi, snr,
      payload_version, node_id, temp_c, humidity_pct, battery_mv, status_flags,
      record_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(dev_eui, fcnt) DO UPDATE SET
      rx_time=excluded.rx_time,
      rssi=excluded.rssi,
      snr=excluded.snr,
      payload_version=excluded.payload_version,
      node_id=excluded.node_id,
      temp_c=excluded.temp_c,
      humidity_pct=excluded.humidity_pct,
      battery_mv=excluded.battery_mv,
      status_flags=excluded.status_flags,
      record_json=excluded.record_json
    ;
    """

    BAD_INSERT_SQL = """
    INSERT INTO bad_packets (rx_time, dev_eui, fcnt, error, received_at_unix)
    VALUES (?, ?, ?, ?, ?);
    """

    def __init__(self, db_path: str, commit_every: int = 1):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # timeout helps a lot on Windows if the file is briefly busy
        self.conn = sqlite3.connect(self.db_path.as_posix(), timeout=30)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self.conn.execute("PRAGMA busy_timeout=30000;")  # 30s wait instead of immediate lock error

        self.conn.executescript(self.SCHEMA_SQL)
        self.conn.commit()

        self._commit_every = max(1, int(commit_every))
        self._pending = 0

    def write(self, record: dict) -> None:
        vals = (
            record["rx_time"],
            record["dev_eui"],
            int(record["fcnt"]),
            float(record["rssi"]) if record.get("rssi") is not None else None,
            float(record["snr"]) if record.get("snr") is not None else None,
            int(record.get("payload_version")) if record.get("payload_version") is not None else None,
            int(record.get("node_id")) if record.get("node_id") is not None else None,
            float(record.get("temp_c")) if record.get("temp_c") is not None else None,
            float(record.get("humidity_pct")) if record.get("humidity_pct") is not None else None,
            int(record.get("battery_mv")) if record.get("battery_mv") is not None else None,
            int(record.get("status_flags")) if record.get("status_flags") is not None else None,
            json.dumps(record),
        )

        self.conn.execute(self.INSERT_SQL, vals)
        self._pending += 1
        if self._pending >= self._commit_every:
            self.conn.commit()
            self._pending = 0

    def write_error(self, uplink: dict, error_message: str) -> None:
        vals = (
            uplink.get("rx_time"),
            uplink.get("dev_eui"),
            uplink.get("fcnt"),
            error_message,
            int(time.time()),
        )
        self.conn.execute(self.BAD_INSERT_SQL, vals)
        self._pending += 1
        if self._pending >= self._commit_every:
            self.conn.commit()
            self._pending = 0

    def flush(self) -> None:
        if self._pending:
            self.conn.commit()
            self._pending = 0

    def close(self) -> None:
        self.flush()
        self.conn.close()