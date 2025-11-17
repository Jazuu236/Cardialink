from machine import ADC, Pin
import time

DYNAMIC_CACHE = []
PEAK_CACHE = []

class cBeat:
    def __init__(self, timestamp, value):
        self.timestamp = timestamp
        self.value = value
    def age(self):
        return time.ticks_diff(time.ticks_ms(), self.timestamp)
    


LED_PINS = [20, 21, 22]
leds = [Pin(pin, Pin.OUT) for pin in LED_PINS]

def get_reading_quality(value):
    global DYNAMIC_CACHE
    if (value < 1.01):
        return("VERY BAD")
    elif (value < 1.02):
        return("BAD")
    elif (value < 1.03):
        return("OK")
    elif (value < 1.04):
        return("GOOD")
    else:
        return("VERY GOOD")
    
def add_to_peak_cache(beat):
    global PEAK_CACHE
    PEAK_CACHE.append(beat)
    #Remove old beats
    PEAK_CACHE = [b for b in PEAK_CACHE if b.age() < 5_000]
    
def get_percent_prepared():
    global DYNAMIC_CACHE
    return (len(DYNAMIC_CACHE) / 5)
        
def cache_update(value):
    global DYNAMIC_CACHE
    DYNAMIC_CACHE.append(value)
    if len(DYNAMIC_CACHE) > 500: #Keeping 500 readings
        DYNAMIC_CACHE.pop(0)
    return sum(DYNAMIC_CACHE) // len(DYNAMIC_CACHE)

def cache_get_peak_value():
    segment_size = len(DYNAMIC_CACHE) // 12
    peaks = []
    for i in range(12):
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

def clear_cache():
    global DYNAMIC_CACHE
    DYNAMIC_CACHE = []

