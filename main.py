"""
Entry point: wires together
GatewaySimulator -> process_uplink -> StdoutJsonSink
"""

from gateway_ingest.simulator import GatewaySimulator
from base_station.ingest_pipeline import process_uplink
from base_station.sinks import StdoutJsonSink, JsonlFileSink, ErrorLogSink

def main():
    sim = GatewaySimulator(node_ids=(1,2,3), period_s=2.0, bad_rate=0.3)

    stdout_sink = StdoutJsonSink()
    file_sink = JsonlFileSink("data/uplinks.jsonl")
    error_sink = ErrorLogSink("logs/errors.log")

    for uplink in sim.stream():
        record, error = process_uplink(uplink)

        if error:
            print(f"[ERROR] {error}")
            error_sink.write(error)
        else:
            stdout_sink.write(record)
            file_sink.write(record)

if __name__ == "__main__":
    main()