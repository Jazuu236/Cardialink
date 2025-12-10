import ujson
from config import connect_wlan, connect_mqtt, MAC
from history import save_to_history_file

class KubiosHandler:
    def __init__(self):
        self.mqtt_client = None
        self.analysis_result = None
        self.is_connected = False
        self.waiting_for_response = False

    # -------------------------
    # MQTT CONNECT
    # -------------------------
    def connect(self):
        try:
            connect_wlan()
            self.mqtt_client = connect_mqtt()
            self.mqtt_client.set_callback(self.mqtt_callback)

            # SUBSCRIBE TO ALL RESPONSE TOPICS
            self.mqtt_client.subscribe(b"kubios/response")
            self.mqtt_client.subscribe(b"database/response")

            self.is_connected = True
            print("MQTT connected and subscriptions active")
        except Exception as e:
            print("Kubios Connection Error:", e)
            self.is_connected = False

    # -------------------------
    # CALLBACK
    # -------------------------
    def mqtt_callback(self, topic, msg):
        print("\n--- MQTT MESSAGE RECEIVED ---")
        print("Topic:", topic)
        print("Message:", msg)

        try:
            data = ujson.loads(msg.decode())

            # -------------------------
            # KUBIOS RESPONSE
            # -------------------------
            if topic == b"kubios/response":
                if "data" in data and "analysis" in data["data"]:
                    print("Kubios analysis received.")

                    self.analysis_result = data["data"]["analysis"]

                    save_to_history_file(self.analysis_result)

                    # NOW SEND TO DATABASE VIA MQTT (NOT HTTP)
                    self.send_device_add()
                    self.send_patient_add()
                    self.send_patient_list()
                    self.send_record_add(self.analysis_result)

            # -------------------------
            # DATABASE RESPONSE
            # -------------------------
            elif topic == b"database/response":
                print("Database response:", data)

        except Exception as e:
            print("JSON Parsing Error:", e)

        finally:
            self.waiting_for_response = False

    # -------------------------
    # SEND KUBIOS REQUEST
    # -------------------------
    def send_analysis_request(self, ppi_data):
        if not self.is_connected:
            self.connect()
        if not self.is_connected or self.mqtt_client is None:
            raise OSError("No connection to Kubios/MQTT")

        clean_ppi = [int(x) for x in ppi_data]
        payload = ujson.dumps({
            "mac": MAC,
            "type": "RRI",
            "data": clean_ppi,
            "analysis": {"type": "readiness"}
        })

        print("\nSending Kubios request...")
        self.mqtt_client.publish(b"kubios/request", payload)

        self.waiting_for_response = True
        self.analysis_result = None

    def check_messages(self):
        if self.is_connected:
            try:
                self.mqtt_client.check_msg()
            except Exception as e:
                print("MQTT Check Error:", e)

    # -------------------------
    # DATABASE MQTT CALLS
    # -------------------------

    def send_device_add(self):
        print("Sending device registration...")
        payload = ujson.dumps({
            "mac": MAC,
            "device_name": "Cardialink"
        })
        self.mqtt_client.publish(b"database/devices/add", payload)

    def send_patient_add(self, name="Matti Meikalainen"):
        print("Adding patient...")
        payload = ujson.dumps({
            "mac": MAC,
            "patient_name": name
        })
        self.mqtt_client.publish(b"database/patients/add", payload)

    def send_patient_list(self):
        print("Requesting patient list...")
        payload = ujson.dumps({"mac": MAC})
        self.mqtt_client.publish(b"database/patients/list", payload)

    def send_record_add(self, analysis):
        print("Sending record...")

        payload = ujson.dumps({
            "mac": MAC,
            "timestamp": 123456789,
            "mean_hr": analysis["mean_hr_bpm"],
            "mean_ppi": analysis["mean_rr_ms"],
            "rmssd": analysis["rmssd_ms"],
            "sdnn": analysis["sdnn_ms"],
            "sns": analysis["sns_index"],
            "pns": analysis["pns_index"],
        })

        self.mqtt_client.publish(b"database/records/add", payload)

