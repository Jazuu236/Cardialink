from config import connect_wlan, connect_mqtt, MAC
import time
import ujson
from history import save_to_history_file

# Connect to WIFI, MQTT and Synctime
connect_wlan()
mqtt_client = connect_mqtt()

# MQTT CALLBACK
def mqtt_callback(topic, msg):
    print("Raw MQTT msg:", msg)
    try:
        data = ujson.loads(msg.decode())
        if "data" in data and "analysis" in data["data"]:
            analysis = data["data"]["analysis"]
            # Print Values
            print("Mean HR: {:.0f}".format(analysis.get("mean_hr_bpm", 0)))
            print("Mean PPI: {:.0f}".format(analysis.get("mean_rr_ms",0)))
            print("RMSSD: {:.0f}".format(analysis.get("rmssd_ms",0)))
            print("SDNN: {:.0f}".format(analysis.get("sdnn_ms", 0)))
            print("SNS: {:.2f}".format(analysis.get("sns_index", 0)))
            print("PNS: {:.2f}".format(analysis.get("pns_index", 0)))
            print("Stress Index: {:.2f}".format(analysis.get("stress_index", 0)))
            print("Physiological age: {:.0f}".format(analysis.get("physiological_age", 0)))
            print("PNS Index: {:.2f}".format(analysis.get("pns_index", 0)))
            print("SNS Index: {:.2f}".format(analysis.get("sns_index", 0)))
            print("Readiness: {:.2f}".format(analysis.get("readiness", 0)))
            print("SD1: {:.2f}".format(analysis.get("sd1_ms", 0)))
            print("SD2: {:.2f}".format(analysis.get("sd2_ms", 0)))

            # Save to history
            save_to_history_file(analysis)
        else:
            print("No analysis field in response:", data)

    except Exception as e:
        print("JSON parse error:", e)

# Subscribe and set callback
mqtt_client.set_callback(mqtt_callback)
mqtt_client.subscribe(b"kubios/response")

# Data
peak_to_peak_interval = [929, 848, 873, 862, 946, 817, 874, 828, 829, 850, 766, 807, 860, 868, 861, 823, 896, 866, 868, 812, 841, 848, 855, 819, 916, 875, 837, 885, 805, 874, 789, 820, 802, 838, 819, 885, 874, 850, 828, 815, 897, 836, 826, 895, 855, 829, 794, 875, 870, 834, 878, 741, 847, 823, 889, 925, 838, 834, 928, 775, 841, 936, 846, 883, 909, 740, 891, 877, 834, 911, 864, 899, 782, 824, 830, 817, 864, 829, 795, 778, 803, 954, 853, 897, 835, 823, 881, 818, 786, 945, 752, 809, 850, 904, 778, 809, 817, 888, 831, 864]

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

