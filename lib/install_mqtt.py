import mip
import network
from time import sleep

SSID = "KME759_Group_1"
PASSWORD = "!Paska123!"
BROKER_IP = "192.168.1.253"

def connect_wlan():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    while wlan.isconnected() == False:
        print("Connecting... ")
        sleep(1)

    print("Connection successful. Pico IP:", wlan.ifconfig()[0])

def install_mqtt():
    try:
        mip.install("umqtt.simple")
    except Exception as e:
        print(f"Could not install MQTT: {e}") 

connect_wlan()
install_mqtt()