from machine import ADC, Pin
import time

class cMeasurer:
    CACHETYPE_200 = 0
    CACHETYPE_DYNAMIC = 1
    CACHETYPE_BEATS = 2

    def __init__(self, led_pins=[20, 21, 22]):
        self.CACHE_STORAGE_200 = []  # Stores 200 readings for calibration
        self.CACHE_STORAGE_DYNAMIC = []  # Stores all readings
        self.CACHE_STORAGE_BEATS = []  # Stores detected peaks as cBeat objects
        self.leds = [Pin(pin, Pin.OUT) for pin in led_pins]
        self.PEAK_WAS_ALREADY_RECORDED = False
        self.temp_restrict_updates = False

    class cBeat:
        def __init__(self, timestamp_ms):
            self.timestamp_ms = timestamp_ms

        def age(self):
            return time.ticks_diff(time.ticks_ms(), self.timestamp_ms)

    def add_to_beat_cache(self, beat):
        self.CACHE_STORAGE_BEATS.append(beat)
        # Keep only beats within last 30 seconds
        self.CACHE_STORAGE_BEATS = [b for b in self.CACHE_STORAGE_BEATS if b.age() <= 30000]

        for i in range(1, len(self.CACHE_STORAGE_BEATS)):
            ppi = self.CACHE_STORAGE_BEATS[i].age() - self.CACHE_STORAGE_BEATS[i - 1].age()
            if -(ppi) < 300:
                # Remove earlier beat
                self.CACHE_STORAGE_BEATS.pop(i - 1)
            elif -(ppi) > 2000:
                # Clear entire cache
                self.CACHE_STORAGE_BEATS = []
                break

    def get_beat_cache_length(self):
        return len(self.CACHE_STORAGE_BEATS)

    def cache_update(self, cache_type, value):
        if cache_type == self.CACHETYPE_200:
            self.CACHE_STORAGE_200.append(value)
            if len(self.CACHE_STORAGE_200) > 200:
                self.CACHE_STORAGE_200.pop(0)
            return True
        elif cache_type == self.CACHETYPE_DYNAMIC:
            self.CACHE_STORAGE_DYNAMIC.append(value)
            return True
        else:
            raise ValueError(f"Measurer.cache_update called with invalid cache_type: {cache_type}")

    def clear_cache(self, cache_type):
        if cache_type == self.CACHETYPE_200:
            self.CACHE_STORAGE_200 = []
        elif cache_type == self.CACHETYPE_DYNAMIC:
            self.CACHE_STORAGE_DYNAMIC = []
        elif cache_type == self.CACHETYPE_BEATS:
            self.CACHE_STORAGE_BEATS = []
        else:
            raise ValueError(f"Measurer.clear_cache called with invalid cache_type: {cache_type}")

    def clear_cache_with_limit(self, cache_type, limit):
        if cache_type == self.CACHETYPE_BEATS:
            while len(self.CACHE_STORAGE_BEATS) > limit:
                self.CACHE_STORAGE_BEATS.pop(0)
        elif cache_type == self.CACHETYPE_200:
            while len(self.CACHE_STORAGE_200) > limit:
                self.CACHE_STORAGE_200.pop(0)
        elif cache_type == self.CACHETYPE_DYNAMIC:
            while len(self.CACHE_STORAGE_DYNAMIC) > limit:
                self.CACHE_STORAGE_DYNAMIC.pop(0)

    def cache_get_peak_value(self, cache_type):
        if cache_type == self.CACHETYPE_200:
            return max(self.CACHE_STORAGE_200) if self.CACHE_STORAGE_200 else 0
        elif cache_type == self.CACHETYPE_DYNAMIC:
            return max(self.CACHE_STORAGE_DYNAMIC) if self.CACHE_STORAGE_DYNAMIC else 0
        else:
            raise ValueError(f"Measurer.cache_get_peak_value called with invalid cache_type: {cache_type}")

    def cache_get_average_value(self, cache_type):
        if cache_type == self.CACHETYPE_200:
            return sum(self.CACHE_STORAGE_200) / len(self.CACHE_STORAGE_200) if self.CACHE_STORAGE_200 else 0
        elif cache_type == self.CACHETYPE_DYNAMIC:
            return sum(self.CACHE_STORAGE_DYNAMIC) / len(self.CACHE_STORAGE_DYNAMIC) if self.CACHE_STORAGE_DYNAMIC else 0
        else:
            raise ValueError(f"Measurer.cache_get_average_value called with invalid cache_type: {cache_type}")

    def cache_get_peak_ratio(self, cache_type):
        if cache_type == self.CACHETYPE_200:
            cache = self.CACHE_STORAGE_200
        elif cache_type == self.CACHETYPE_DYNAMIC:
            cache = self.CACHE_STORAGE_DYNAMIC
        else:
            raise ValueError(f"Measurer.cache_get_peak_ratio called with invalid cache_type: {cache_type}")

        if not cache:
            return 0
        average = sum(cache) / len(cache)
        peak = max(cache)
        return peak / average if average != 0 else 0

    def dynamic_cache_get_average_peak_value(self):
        if not self.CACHE_STORAGE_DYNAMIC:
            return 0
        segment_length = 200  # 2 seconds at 100Hz
        num_segments = len(self.CACHE_STORAGE_DYNAMIC) // segment_length
        if num_segments == 0:
            return 0
        peaks = [max(self.CACHE_STORAGE_DYNAMIC[i * segment_length:(i + 1) * segment_length]) for i in range(num_segments)]
        return sum(peaks) / len(peaks)

    def control_led(self, signal):
        self.leds[0].value(signal)

    @staticmethod
    def ppi_filter_abnormalities(ppi_data, max_deviation_percentage):
        if len(ppi_data) < 2:
            return ppi_data
        average_ppi = sum(ppi_data) / len(ppi_data)
        return [ppi for ppi in ppi_data if abs(ppi - average_ppi) / average_ppi * 100 <= max_deviation_percentage]