from config import connect_wlan, connect_mqtt, MAC
import time
import ujson

# Connect to WIFI and MQTT
connect_wlan()
mqtt_client = connect_mqtt()

# MQTT CALLBACK
def mqtt_callback(topic, msg):
    print("Raw MQTT msg:", msg)  # bytes

    try:
        data = ujson.loads(msg.decode())
        analysis = data["data"]["analysis"]

        timestamp = analysis.get("create_timestamp")
        mean_hr = analysis.get("mean_hr_bpm")
        mean_ppi = analysis.get("mean_rr_ms")
        RMSSD = analysis.get("rmssd_ms")
        SDNN = analysis.get("sdnn_ms")
        SNS = analysis.get("sns_index")
        PNS = analysis.get("pns_index")
        stress_index = analysis.get("stress_index")

        print("Time:", timestamp)
        print("Mean HR:", mean_hr)
        print("Mean PPI:", mean_ppi)
        print("RMSSD:", RMSSD)
        print("SDNN:", SDNN)
        print("SNS:", SNS)
        print("PNS:", PNS)
        print("stress Index:", stress_index)
        
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

