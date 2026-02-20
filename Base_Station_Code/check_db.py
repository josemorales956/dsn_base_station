import sqlite3

conn = sqlite3.connect("data/readings.sqlite3")

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