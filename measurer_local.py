from machine import ADC, Pin
import time

LED_PINS = [20, 21, 22]

leds = [Pin(pin, Pin.OUT) for pin in LED_PINS]

DYNAMIC_CACHE = []

def print_reading_quality(value):
    global DYNAMIC_CACHE
    if (value < 1.01):
        print("read quality: VERY BAD")
    elif (value < 1.02):
        print("read quality: BAD")
    elif (value < 1.03):
        print("read quality: OK")
    elif (value < 1.04):
        print("read quality: GOOD")
    else:
        print("read quality: VERY GOOD: " + str(value))
        
    print("INITALIZATION: " + str(int(len(DYNAMIC_CACHE )/ 3)) + "%")
        
def cache_update(value):
    global DYNAMIC_CACHE
    DYNAMIC_CACHE.append(value)
    if len(DYNAMIC_CACHE) > 300: #Keeping 300 readings
        DYNAMIC_CACHE.pop(0)
    return sum(DYNAMIC_CACHE) // len(DYNAMIC_CACHE)

def cache_get_peak_value():
    segment_size = len(DYNAMIC_CACHE) // 12
    peaks = []
    for i in range(10):
        segment = DYNAMIC_CACHE[i*segment_size:(i+1)*segment_size]
        if segment:
            peaks.append(max(segment))
    if peaks:
        return sum(peaks) // len(peaks)
    return 1

def cache_get_peak_ratio():
    peak_value = cache_get_peak_value()
    if peak_value == 0:
        return 0
    return peak_value / (sum(DYNAMIC_CACHE) / len(DYNAMIC_CACHE))


def control_led(signal):
    leds[0].value(signal)

# Initialize ADC on pin 27 (ADC1)
adc = ADC(Pin(27))

# Sampling interval (adjust as needed)
delay_ms = 10  # 100 samples/sec approx

LEGAL_LOW = 30_000
LEGAL_HIGH = 35_000


while True:
    raw_value = adc.read_u16()  # Read 16-bit ADC value (0–65535)
    if ((raw_value < LEGAL_LOW) or (raw_value > LEGAL_HIGH)):
        continue 
    avg_value = cache_update(raw_value)
    #print("val: " + str(raw_value) + "avg:" + str(avg_value) + "len:" + str(len(DYNAMIC_CACHE)) + "tresh:" + str((cache_get_peak_value()))+ " R: " + str(cache_get_peak_ratio()))
    print_reading_quality(cache_get_peak_ratio())
    if (raw_value > cache_get_peak_value()):
        control_led(1)
    else:
        control_led(0)

    time.sleep_ms(delay_ms)
