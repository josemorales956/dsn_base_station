"""
Entry point: wires together
GatewaySimulator -> process_uplink -> StdoutJsonSink
"""

from gateway_ingest.simulator import GatewaySimulator
from base_station.ingest_pipeline import process_uplink
from base_station.sinks import StdoutJsonSink, JsonlFileSink, ErrorLogSink, SqliteSink


def main():
    sim = GatewaySimulator(node_ids=(1, 2, 3), period_s=2.0, bad_rate=0.3)

    stdout_sink = StdoutJsonSink()
    file_sink = JsonlFileSink("data/uplinks.jsonl")
    error_sink = ErrorLogSink("logs/errors.log")
    db_sink = SqliteSink("data/readings.sqlite3", commit_every=10)  # batch commits

    try:
        for uplink in sim.stream():
            record, error = process_uplink(uplink)

            if error:
                print(f"[ERROR] {error}")
                error_sink.write(error)

                # NEW: store errors in SQLite bad_packets table
                db_sink.write_error(uplink, error)
            else:
                stdout_sink.write(record)
                file_sink.write(record)
                db_sink.write(record)
    finally:
        db_sink.close()


if __name__ == "__main__":
    main()