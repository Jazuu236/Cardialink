import ujson
from config import connect_wlan, connect_mqtt, MAC
from history import save_to_history_file

class KubiosHandler:
    def __init__(self):
        self.mqtt_client = None
        self.analysis_result = None
        self.is_connected = False
        self.waiting_for_response = False

    def connect(self):
        try:
            connect_wlan()
            self.mqtt_client = connect_mqtt()
            self.mqtt_client.set_callback(self.mqtt_callback)
            self.mqtt_client.subscribe(b"kubios/response")
            self.is_connected = True
        except Exception as e:
            print("Kubios Connection Error:", e)
            self.is_connected = False

    def mqtt_callback(self, topic, msg):
        try:
            data = ujson.loads(msg.decode())
            if "data" in data and "analysis" in data["data"]:
                self.analysis_result = data["data"]["analysis"]
                save_to_history_file(self.analysis_result)
        except Exception as e:
            print("JSON Parsing Error:", e)
        finally:
            self.waiting_for_response = False

    def send_analysis_request(self, ppi_data):
        if not self.is_connected:
            self.connect()
        if not self.is_connected or self.mqtt_client is None:
            raise OSError("No connection to Kubios/MQTT")

        clean_ppi = [int(x) for x in ppi_data]
        kubios_payload = ('{'
            '"mac": "' + MAC + '",'
            '"type": "RRI",'
            '"data": ' + str(clean_ppi) + ','
            '"analysis": { "type": "readiness" }'
            '}')

        self.mqtt_client.publish(b"kubios/request", kubios_payload)
        self.waiting_for_response = True
        self.analysis_result = None

    def check_messages(self):
        if self.is_connected and self.waiting_for_response:
            try:
                self.mqtt_client.check_msg()
            except Exception as e:
                print("MQTT Check Error:", e)
