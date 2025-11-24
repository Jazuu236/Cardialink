from config import connect_wlan, connect_mqtt, MAC
import time
import json

# Connect to WIFI and MQTT
connect_wlan()
mqtt_client = connect_mqtt()

# Subscribe to Kubios
mqtt_client.subscribe(b"kubios/response")

# Building JSON payload
kubios_payload = json.dumps({
    "mac": MAC,
    "type": "PPI",
    "data": peak_to_peak_interval_data,
    "analysis": {"type": "readiness"}
})

# Publish request
mqtt_client.publish(b"kubios/request", kubios_payload)

# Wait for responses
while True:
    try:
        mqtt_client.wait_msg()
    except Exception as e:
        print("MQTT wait error:", e)
        time.sleep(1)