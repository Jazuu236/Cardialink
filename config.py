import network
from time import sleep
from umqtt.simple import MQTTClient

#Finds the Pico's MAC 
wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.active(True)
wlan_mac = wlan_sta.config('mac')
print(wlan_mac.hex().upper())

#Network config
SSID = "KME759_Group_1"
PASSWORD = "!Paska123!"
BROKER_IP = "192.168.1.253"
BROKER_PORT = 21883
MAC = wlan_mac.hex().upper()

#Connects the Pico to WI-FI
def connect_wlan():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        print("Connecting to WiFi...")
        sleep(1)

    print("WiFi connected. Pico IP:", wlan.ifconfig()[0])
    return wlan

#Callback function for received MQTT messages
def on_message(topic, msg):
    print("Received MQTT message:")
    print("  Topic :", topic)
    print("  Msg   :", msg)

#Connects to the MQTT broker
def connect_mqtt():
    client = MQTTClient(client_id=b"", server=BROKER_IP, port=BROKER_PORT)
    client.set_callback(on_message)
    client.connect(clean_session=True)

    print("MQTT connected to {}:{}".format(BROKER_IP, BROKER_PORT))
    return client