import network
from time import sleep
from machine import RTC
from umqtt.simple import MQTTClient
import ntptime
import time

wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.active(True)
wlan_mac = wlan_sta.config('mac')

SSID = "KME759_Group_1"
PASSWORD = "!Paska123!"
BROKER_IP = "192.168.1.253"
BROKER_PORT = 21883
MAC = wlan_mac.hex().upper()

# Time sync
def sync_time():
    try:
        print("Synchronizing time from NTP...")
        ntptime.settime()

        UTC_OFFSET = 7200 #Time offset
        actual_time = time.time() + UTC_OFFSET
        
        tm = time.localtime(actual_time)
        RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
        
        print("Time synchronized:", time.localtime())
    except Exception as e:
        print("Time sync failed:", e)
        
# Connects the Pico to WI-FI
def connect_wlan():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if wlan.isconnected():
        if time.localtime()[0] < 2024:
             sync_time()
        return wlan

    print("Connecting to WiFi...")
    wlan.connect(SSID, PASSWORD)
    
    max_retries = 10
    while not wlan.isconnected() and max_retries > 0:
        sleep(1)
        max_retries -= 1
        
    if wlan.isconnected():
        print("WiFi connected!")
        sync_time()
    else:
        print("WiFi connection failed!")
        
    return wlan

# Connects to the MQTT broker
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
