from machine import ADC, Pin
import time
import panic

CACHETYPE_200 = 0
CACHETYPE_DYNAMIC = 1

CACHE_STORAGE_200 = [] #This cache has 200 readings (2 seconds of data), it is used for calibrating the peak value.
CACHE_STORAGE_DYNAMIC = [] #This cache stores every reading.


LED_PINS = [20, 21, 22]
leds = [Pin(pin, Pin.OUT) for pin in LED_PINS]
    
def add_to_peak_cache(beat):
    global PEAK_CACHE
    PEAK_CACHE.append(beat)
    #Remove old beats
    PEAK_CACHE = [b for b in PEAK_CACHE if b.age() < 5_000]
    
        
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
    if cache_type == CACHETYPE_200:
        CACHE_STORAGE_200 = []
    elif cache_type == CACHETYPE_DYNAMIC:
        CACHE_STORAGE_DYNAMIC = []
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

def control_led(signal):
    leds[0].value(signal)