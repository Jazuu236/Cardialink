import mip
import urequests
import os

# Files
lib_url = "https://gitlab.metropolia.fi/lansk/pico-lib/-/raw/main"
files = ["fifo.py", "filefifo.py", "led.py", "piotimer.py", "ssd1306.mpy"]


# Check and create lib folder
try:
    os.mkdir("lib")
except OSError:
    print("LIB folder already exists!")

for fname in files:
    url = lib_url + "/" + fname
    print(f"Downloading: {fname}!")
    r = urequests.get(url)
    with open("lib/" + fname, "wb") as f:
        f.write(r.content)
    r.close()

print("All libraries downloaded.")

# MQTT download
def install_mqtt():
    try:
        mip.install("umqtt.simple")
    except Exception as e:
        print(f"Could not install MQTT: {e}")

install_mqtt()
