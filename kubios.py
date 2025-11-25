from config import connect_wlan, connect_mqtt, MAC
import time
import ujson
from history import save_to_history_file

# Connect to WIFI and MQTT
connect_wlan()
mqtt_client = connect_mqtt()

# MQTT CALLBACK
def mqtt_callback(topic, msg):
    print("Raw MQTT msg:", msg)  # bytes

    try:
        data = ujson.loads(msg.decode())
        analysis = data["data"]["analysis"]

        print("Mean HR:", analysis.get("mean_hr_bpm"))
        print("Mean PPI:", analysis.get("mean_rr_ms"))
        print("RMSSD:", analysis.get("rmssd_ms"))
        print("SDNN:", analysis.get("sdnn_ms"))
        print("SNS:", analysis.get("sns_index"))
        print("PNS:", analysis.get("pns_index"))
        print("Stress Index:", analysis.get("stress_index"))
    
        # Safe Kubios data to history
        save_to_history_file(analysis)

    except Exception as e:
        print("JSON parse error:", e)

# Subscribe and set callback
mqtt_client.set_callback(mqtt_callback)
mqtt_client.subscribe(b"kubios/response")

# Data
peak_to_peak_interval = []

# Build JSON payload
kubios_payload = (
    '{'
    '"mac": "' + MAC + '",'
    '"type": "RRI",'
    '"data": ' + str(peak_to_peak_interval) + ','
    '"analysis": { "type": "readiness" }'
    '}'
)

# Publish request
mqtt_client.publish(b"kubios/request", kubios_payload)
print("Analyzing...")

# MAIN LOOP
while True:
    try:
        mqtt_client.wait_msg()   # waits for MQTT → triggers callback
    except Exception as e:
        print("MQTT wait error:", e)
        time.sleep(1)


