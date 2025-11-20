import network
from time import sleep
from umqtt.simple import MQTTClient

#MAC
wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.active(True)
wlan_mac = wlan_sta.config('mac')
print(wlan_mac.hex().upper())

#Network
SSID = "KME759_Group_1"
PASSWORD = "!Paska123!"
BROKER_IP = "192.168.1.253"
BROKER_PORT = 21883
MAC = wlan_mac.hex().upper()

def connect_wlan():
    wlan = network.WLAN(network.STA_IF)  # "STA_IF" = station mode (client)
    wlan.active(True)                    # turn Wi-Fi on
    wlan.connect(SSID, PASSWORD)         # start connection to router
    while not wlan.isconnected():
        print("Connecting to WiFi...")
        sleep(1)

    print("WiFi connected. Pico IP:", wlan.ifconfig()[0])
    return wlan

def on_message(topic, msg):
    print("Received MQTT message:")
    print("  Topic :", topic)
    print("  Msg   :", msg)

def connect_mqtt():
    client = MQTTClient(client_id=b"", server=BROKER_IP, port=BROKER_PORT)
    client.set_callback(on_message)
    client.connect(clean_session=True)

    print("MQTT connected to {}:{}".format(BROKER_IP, BROKER_PORT))
    return client

# MAIN PROGRAM
if __name__ == "__main__":
    # 1. Connect Pico W to Wi-Fi
    connect_wlan()
    # 2. Connect Pico W to the MQTT broker (kubios-proxy)
    try:
        mqtt_client = connect_mqtt()
    except Exception as e:
        print("Failed to connect to MQTT:", e)
        # If we cannot connect to MQTT, there is no point continuing.
        raise SystemExit()

    # 3. Subscribe FIRST so we don't miss the response
    mqtt_client.subscribe(b"kubios/response")
    print("Subscribed to kubios/response")

    # 4. Copy the Kubios request payload from info page
    kubios_payload = (
        '{'
        '"mac": "' + MAC + '",'
        '"type": "PPI",'
        '"data": [828, 836, 852, 760, 800, 796, 856, 824, 808, 776, '
                  '724, 816, 800, 812, 812, 812, 756, 820, 812, 800],'
        '"analysis": { "type": "readiness" }'
        '}'
    )

    # MQTT topic for sending requests to Kubios via kubios-proxy
    kubios_topic = b"kubios/request"

    # 5. Publish the Kubios request ONCE
    try:
        mqtt_client.publish(kubios_topic, kubios_payload)
        print("Sent Kubios request:")
        print("  Topic  :", kubios_topic)
        print("  Payload:", kubios_payload)
    except Exception as e:
        print("Failed to send Kubios request:", e)

    # 6. Wait for responses FOREVER (blocking loop)
    print("Waiting for Kubios responses...")
    while True:
        try:
            mqtt_client.wait_msg()   # This will block until a message arrives
        except Exception as e:
            print("Error while waiting for message:", e)
            sleep(1)
