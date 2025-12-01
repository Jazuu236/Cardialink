from machine import ADC, Pin
import time
import panic

CACHETYPE_200 = 0
CACHETYPE_DYNAMIC = 1
CACHETYPE_BEATS = 2

CACHE_STORAGE_200 = [] #This cache has 200 readings (2 seconds of data), it is used for calibrating the peak value.
CACHE_STORAGE_DYNAMIC = [] #This cache stores every reading.
CACHE_STORAGE_BEATS = [] #This cache stores detected peaks as cBeat objects.

PEAK_WAS_ALREADY_RECORDED = False

class cBeat:
    def __init__(self, timestamp_ms):
        self.timestamp_ms = timestamp_ms
        
    def age(self):
        return time.ticks_diff(time.ticks_ms(), self.timestamp_ms)

LED_PINS = [20, 21, 22]
leds = [Pin(pin, Pin.OUT) for pin in LED_PINS]
    
def add_to_beat_cache(beat):
    global CACHE_STORAGE_BEATS
    CACHE_STORAGE_BEATS.append(beat)
    CACHE_STORAGE_BEATS = [b for b in CACHE_STORAGE_BEATS if b.age() <= 30000]
    #Loop thru the entire beat cache, and if the difference between 2 beats is less than 300 ms, or greater than 2000ms, clear the beat cache
    for i in range(1, len(CACHE_STORAGE_BEATS)):
        ppi = CACHE_STORAGE_BEATS[i].age() - CACHE_STORAGE_BEATS[i-1].age()
        if -(ppi) < 300 :
            #Remove the earlier beat
            CACHE_STORAGE_BEATS.pop(i-1)
        elif -(ppi) > 2000 :
            #Clear the entire cache
            CACHE_STORAGE_BEATS = []
            break



def get_beat_cache_length():
    global CACHE_STORAGE_BEATS
    return len(CACHE_STORAGE_BEATS)
    
        
def cache_update(cache_type, value):
    global CACHE_STORAGE_200
    global CACHE_STORAGE_DYNAMIC
    if cache_type == CACHETYPE_200:
        CACHE_STORAGE_200.append(value)
        if len(CACHE_STORAGE_200) > 200: #Keeping 200 readings
            CACHE_STORAGE_200.pop(0)
        return True
    elif cache_type == CACHETYPE_DYNAMIC:
        CACHE_STORAGE_DYNAMIC.append(value)
        return True
    else:
        panic.panic("measurer.cache_update called with invalid cache_type: " + str(cache_type))
        return False
    
def clear_cache(cache_type):
    global CACHE_STORAGE_200
    global CACHE_STORAGE_DYNAMIC
    global CACHE_STORAGE_BEATS
    if cache_type == CACHETYPE_200:
        CACHE_STORAGE_200 = []
    elif cache_type == CACHETYPE_DYNAMIC:
        CACHE_STORAGE_DYNAMIC = []
    elif cache_type == CACHETYPE_BEATS:
        CACHE_STORAGE_BEATS = []
    else:
        panic.panic("measurer.clear_cache called with invalid cache_type: " + str(cache_type))


def cache_get_peak_value(cache_type):
    if cache_type == CACHETYPE_200:
        if len(CACHE_STORAGE_200) == 0:
            return 0
        return max(CACHE_STORAGE_200)
    elif cache_type == CACHETYPE_DYNAMIC:
        if len(CACHE_STORAGE_DYNAMIC) == 0:
            return 0
        return max(CACHE_STORAGE_DYNAMIC)
    else:
        panic.panic("measurer.cache_get_peak_value called with invalid cache_type: " + str(cache_type))
        return 0

def cache_get_peak_ratio(cache_type):
    if cache_type == CACHETYPE_200:
        if len(CACHE_STORAGE_200) == 0:
            return 0
        average = sum(CACHE_STORAGE_200) / len(CACHE_STORAGE_200)
        peak = max(CACHE_STORAGE_200)
        if average == 0:
            return 0
        return peak / average
    elif cache_type == CACHETYPE_DYNAMIC:
        if len(CACHE_STORAGE_DYNAMIC) == 0:
            return 0
        average = sum(CACHE_STORAGE_DYNAMIC) / len(CACHE_STORAGE_DYNAMIC)
        peak = max(CACHE_STORAGE_DYNAMIC)
        if average == 0:
            return 0
        return peak / average
    else:
        panic.panic("measurer.cache_get_peak_ratio called with invalid cache_type: " + str(cache_type))
        return 0
    
def cache_get_average_value(cache_type):
    if cache_type == CACHETYPE_200:
        if len(CACHE_STORAGE_200) == 0:
            return 0
        return sum(CACHE_STORAGE_200) / len(CACHE_STORAGE_200)
    elif cache_type == CACHETYPE_DYNAMIC:
        if len(CACHE_STORAGE_DYNAMIC) == 0:
            return 0
        return sum(CACHE_STORAGE_DYNAMIC) / len(CACHE_STORAGE_DYNAMIC)
    else:
        panic.panic("measurer.cache_get_average_value called with invalid cache_type: " + str(cache_type))
        return 0

def dynamic_cache_get_average_peak_value():
    #Split the cache into 2 second segments, get the peak of each segment, then average those peaks.
    global CACHE_STORAGE_DYNAMIC
    if len(CACHE_STORAGE_DYNAMIC) == 0:
        return 0
    segment_length = 200 #2 seconds at 100Hz
    num_segments = len(CACHE_STORAGE_DYNAMIC) // segment_length
    if num_segments == 0:
        return 0
    peaks = []
    for i in range(num_segments):
        segment = CACHE_STORAGE_DYNAMIC[i * segment_length:(i + 1) * segment_length]
        peaks.append(max(segment))
    return sum(peaks) / len(peaks)

def control_led(signal):
    leds[0].value(signal)

def ppi_filter_abnormalities(ppi_data, max_deviation_percentage):
    if len(ppi_data) < 2:
        return ppi_data
    average_ppi = sum(ppi_data) / len(ppi_data)
    filtered_ppi = []
    for ppi in ppi_data:
        deviation = abs(ppi - average_ppi) / average_ppi * 100
        if deviation <= max_deviation_percentage:
            filtered_ppi.append(ppi)

    return filtered_ppi

def clear_cache_with_limit(cache_type, limit):
    global CACHE_STORAGE_BEATS
    if cache_type == CACHETYPE_BEATS:
        while len(CACHE_STORAGE_BEATS) > limit:
            CACHE_STORAGE_BEATS.pop(0)
    
    global CACHE_STORAGE_200
    if cache_type == CACHETYPE_200:
        while len(CACHE_STORAGE_200) > limit:
            CACHE_STORAGE_200.pop(0)
    
    global CACHE_STORAGE_DYNAMIC
    if cache_type == CACHETYPE_DYNAMIC:
        while len(CACHE_STORAGE_DYNAMIC) > limit:
            CACHE_STORAGE_DYNAMIC.pop(0)
    
    return
