import network
from time import sleep

# Network
SSID = "KME759_Group_1"
PASSWORD = "!Paska123!"

def connect_wlan():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    while wlan.isconnected() == False:
        print("Connecting...")
        sleep(1)
    print("Connection successful. Pico IP:", wlan.ifconfig()[0])
    
connect_wlan()