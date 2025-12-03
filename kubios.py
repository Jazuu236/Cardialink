import ujson
import time
from config import connect_wlan, connect_mqtt, MAC
from history import save_to_history_file

class KubiosHandler:
    def __init__(self):
        self.mqtt_client = None
        self.analysis_result = None
        self.is_connected = False
        self.waiting_for_response = False

    def connect(self):
        """Connects to WiFi and MQTT if not already connected"""
        try:
            connect_wlan()
            self.mqtt_client = connect_mqtt()
            self.mqtt_client.set_callback(self.mqtt_callback)
            self.mqtt_client.subscribe(b"kubios/response")
            self.is_connected = True
            print("Kubios: Connected to MQTT")
        except Exception as e:
            print("Kubios Connection Error:", e)
            self.is_connected = False

    def mqtt_callback(self, topic, msg):
        """Handles incoming MQTT messages"""
        print("Kubios Response Received")
        try:
            data = ujson.loads(msg.decode())
            if "data" in data and "analysis" in data["data"]:
                self.analysis_result = data["data"]["analysis"]
                # Save to history immediately upon receipt
                save_to_history_file(self.analysis_result)
            else:
                print("No analysis data in response")
        except Exception as e:
            print("JSON Parsing Error:", e)
        finally:
            self.waiting_for_response = False

    def send_analysis_request(self, ppi_data):
        """Sends the PPI data to Kubios via MQTT"""
        # Try to connect
        if not self.is_connected:
            self.connect()
        # If connection failes terminate            
        if not self.is_connected or self.mqtt_client is None:
            raise OSError("No connection to Kubios/MQTT")

        # Build JSON payload
        clean_ppi = [int(x) for x in ppi_data]
        
        kubios_payload = ('{'
            '"mac": "' + MAC + '",'
            '"type": "RRI",'
            '"data": ' + str(clean_ppi) + ','
            '"analysis": { "type": "readiness" }'
            '}')

        print("Sending data to Kubios...")
        self.mqtt_client.publish(b"kubios/request", kubios_payload)
        self.waiting_for_response = True
        self.analysis_result = None

    def check_messages(self):
        """Checks for incoming MQTT messages (non-blocking)"""
        if self.is_connected and self.waiting_for_response:
            try:
                self.mqtt_client.check_msg()
            except Exception as e:
                print("MQTT Check Error:", e)
