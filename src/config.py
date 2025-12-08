import network
from time import sleep
from machine import RTC
from umqtt.simple import MQTTClient
import ntptime
import time

#Finds the Pico's MAC 
wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.active(True)
wlan_mac = wlan_sta.config('mac')

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
    print("WiFi connected!")
    return wlan


#Connects to the MQTT broker
def connect_mqtt():
    try:
        client = MQTTClient(client_id=MAC.encode(), server=BROKER_IP, port=BROKER_PORT)
        client.set_callback(lambda t, m: print("Received message:", t, m))
        client.connect(clean_session=True)
        print("Connected to Server")
        return client
    except Exception as e:
        print("Server connection failed:", e)
        return None
