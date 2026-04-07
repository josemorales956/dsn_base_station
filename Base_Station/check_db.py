import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "readings.sqlite3"

print("Using DB:", DB_PATH)

conn = sqlite3.connect(DB_PATH)

print("Tables:")
print(conn.execute("select name from sqlite_master where type='table'").fetchall())

print("\nRow count:")
print(conn.execute("select count(*) from uplinks").fetchone())

print("\nLast rows:")
print(conn.execute("""
select dev_eui, node_id, rx_time, temp_c, humidity_pct
from uplinks
order by id desc
limit 5
""").fetchall())

print("\nBad packets count:")
print(conn.execute("select count(*) from bad_packets").fetchone())

print("\nUplinks columns:")
print(conn.execute("PRAGMA table_info(uplinks);").fetchall())

conn.close()