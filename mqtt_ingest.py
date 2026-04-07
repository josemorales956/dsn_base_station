import json
import base64
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

from Base_Station.base_station_code.ingest_pipeline import process_uplink
from Base_Station.base_station_code.sinks import SqliteSink, PerNodeJsonlSink



DB_PATH = "data/readings.sqlite3"
sink = SqliteSink(DB_PATH)
per_node_sink = PerNodeJsonlSink("data/per_node")

def chirpstack_to_uplink(msg_dict: dict) -> dict:
    dev_eui = msg_dict["deviceInfo"]["devEui"]
    fcnt = msg_dict["fCnt"]
    rx_info_list = msg_dict.get("rxInfo") or [{}]
    rx_info = rx_info_list[0]
    data_b64 = msg_dict["data"]

    rx_time = (
        msg_dict.get("time")
        or rx_info.get("time")
        or datetime.now(timezone.utc).isoformat()
    )

    uplink = {
        "rx_time": rx_time,
        "dev_eui": dev_eui,
        "fcnt": fcnt,
        "rssi": rx_info.get("rssi"),
        "snr": rx_info.get("snr"),
        "payload_raw": base64.b64decode(data_b64),
    }
    return uplink

def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Connected with reason code:", reason_code)
    client.subscribe("application/+/device/+/event/up")

def on_message(client, userdata, msg):
    print("\n--- MQTT MESSAGE ---")
    print("Topic:", msg.topic)

    try:
        body = json.loads(msg.payload.decode())
        uplink = chirpstack_to_uplink(body)
        record, err = process_uplink(uplink)

        if err:
            print("Pipeline error:", err)
            sink.write_error(uplink, err)
            per_node_sink.write_error({
                "uplink": uplink,
                "error": err,
            })
            return

        sink.write(record)
        per_node_sink.write(record)
        print("Stored record:", record)

    except Exception as e:
        print("Unhandled error:", e)
        try:
            fallback_uplink = {
                "rx_time": None,
                "dev_eui": None,
                "fcnt": None,
            }
            sink.write_error(fallback_uplink, str(e))
            per_node_sink.write_error({
                "uplink": fallback_uplink,
                "error": str(e),
            })
        except Exception:
            pass
        

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_forever()