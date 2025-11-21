from config import connect_wlan, connect_mqtt, MAC
import time

# This MQTT part is from project course material and modified for this
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
        # Peak to peak interval data
        '"data": {peak_to_peak_interval_data},'
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


# There will be more to this
