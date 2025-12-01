import time
import measurer
import panic
import peak_processing
import HRV


class cGUI:
    def __init__(self, oled):
        self.oled = oled

    def draw_page_init(self):
        self.oled.fill(0)
        measurer.control_led(0)
        self.oled.text("Initializing", 0, 0)
        self.oled.show()

    def draw_main_menu(self, current_selection, anim_pos, anim_time):
        self.oled.fill(0)
        if (current_selection == 0):
            self.oled.text("-> Measure HR", 0, 0)
        else:
            self.oled.text("   Measure HR", 0, 0)
        if (current_selection == 1):
            self.oled.text("-> Basic HRV", 0, 10)
        else:
            self.oled.text("   Basic HRV", 0, 10)
        if (current_selection == 2):
            self.oled.text("-> Kubios", 0, 20)
        else:
            self.oled.text("   Kubios", 0, 20)
        if (current_selection == 3):
            self.oled.text("-> History", 0, 30)
        else:
            self.oled.text("   History", 0, 30)
        if (current_selection == 4):
            self.oled.text("-> Settings EXIT", 0, 40)
        else:
            self.oled.text("   Settings EXIT", 0, 40)

        current_time = time.ticks_ms()
        current_time = time.ticks_ms()
        time_diff = time.ticks_diff(current_time, anim_time)
        decay = 1 - min(max(time_diff / 1000, 0), 1)
        base_width = int(self.oled.width * anim_pos)
        line_width = int(base_width * decay)
        if line_width > 0:
            self.oled.hline((self.oled.width - line_width) // 2,
            self.oled.height - 1,
            line_width, 1)
        self.oled.show()

    def draw_ready_to_start(self):
        self.oled.fill(0)
        self.oled.text("READY?", 40, 20)
        self.oled.text("Press to Start", 10, 40)
        self.oled.show()

    def draw_measure_hr(self):
        #Display current read
        if len(measurer.CACHE_STORAGE_BEATS) == 0:
            self.oled.fill(0)
            self.oled.text("Read: N/A", 0, 0)
            self.oled.show()
            return False
        num_beats = measurer.get_beat_cache_length()
        time_since_first_beat = measurer.CACHE_STORAGE_BEATS[0].age() if num_beats > 0 else 0

        if not time_since_first_beat > 0:
            self.oled.fill(0)
            self.oled.text("BPM: N/A", 0, 50)
            self.oled.show()
            return False
        
        #Clear the top 10 pixels
        self.oled.fill_rect(0, 0, self.oled.width, 10, 0)

        if not hasattr(self, "already_cleared"):
            self.already_cleared = True
            self.oled.fill(0)
            self.oled.text("Preparing...", 0, 0)
            self.oled.show()
            return False
        
        if not hasattr(self, "time_started"):
            self.time_started = time.ticks_ms()

        if (self.time_started + 5000) > time.ticks_ms():
            dots = ((time.ticks_ms() // 500) % 4)
            self.oled.text("BPM: " + dots * ".", 0, 0)
            self.oled.show()
        else:
            bpm = (num_beats * 60000) / time_since_first_beat
            self.oled.text("BPM: " + "{0:.1f}".format(bpm), 0, 0)


        graph_width = self.oled.width
        graph_height = 50

        self.oled.fill_rect(0, 10, graph_width, graph_height, 0)

        if len(measurer.CACHE_STORAGE_200) < 2:
            self.oled.text("Graph: N/A", 0, 10)
            self.oled.show()
            return False

        max_value = max(measurer.CACHE_STORAGE_200)
        min_value = min(measurer.CACHE_STORAGE_200)
        value_range = max_value - min_value

        if value_range == 0:
            self.oled.text("Graph: N/A (2)", 0, 10)
            self.oled.show()
            return False

        for i in range(len(measurer.CACHE_STORAGE_200) - 1):
            val1 = measurer.CACHE_STORAGE_200[i]
            val2 = measurer.CACHE_STORAGE_200[i + 1]
            y1 = 10 + graph_height - int(((val1 - min_value) / value_range) * graph_height)
            y2 = 10 + graph_height - int(((val2 - min_value) / value_range) * graph_height)
            x1 = (i * graph_width) // len(measurer.CACHE_STORAGE_200)
            x2 = ((i + 1) * graph_width) // len(measurer.CACHE_STORAGE_200)
            self.oled.line(x1, y1, x2, y2, 1)



        self.oled.show()
        return False


    def draw_measure_hrv(self, start_ts):
        self.oled.fill(0)

        time_remaining = 30_000 - time.ticks_diff(time.ticks_ms(), start_ts)

        self.oled.text("Measuring HRV...", 0, 0)
        self.oled.text("Please wait " + str(max(time_remaining // 1000, 0)) + "s", 0, 10)

        if (time_remaining < 0):
            self.oled.fill(0)

        self.oled.show()

    # Measure Kubios
    def draw_measure_kubios(self, start_ts):
        self.oled.fill(0)

        time_remaining = 30_000 - time.ticks_diff(time.ticks_ms(), start_ts)

        self.oled.text("Kubios Analysis", 0, 0)
        self.oled.text("Measuring...", 0, 10)
        self.oled.text("Wait: " + str(max(time_remaining // 1000, 0)) + "s", 0, 30)

        if (time_remaining < 0):
            self.oled.fill(0)

        self.oled.show()


    def draw_measure_hrv_show_results(self):
        self.oled.fill(0)
        #Calculate the treshold for peak detection
        if len(measurer.CACHE_STORAGE_DYNAMIC) < 2:
            self.oled.text("Measurement failed", 0, 0)
            self.oled.text("Not enough data", 0, 10)
            self.oled.show()
            return
        avg_value = measurer.cache_get_average_value(measurer.CACHETYPE_DYNAMIC)
        threshold = avg_value + (measurer.dynamic_cache_get_average_peak_value() - avg_value) * 0.6


        #Run PPI processing
        detected_peaks = peak_processing.detect_peaks(measurer.CACHE_STORAGE_DYNAMIC, threshold, 10)

        ppi = []

        for i in range(1, len(detected_peaks)):
            ppi.append(detected_peaks[i][0] - detected_peaks[i-1][0])
        
        filtered_ppi = measurer.ppi_filter_abnormalities(ppi, 33) #Filter all abnormalities greater than 33% deviation (pos <-> neg)

        hrv_results = HRV.hrv_analysis(filtered_ppi)
        #Display everything
        self.oled.text("HRV Results:", 0, 0)
        self.oled.text("Mean PPI: " + str(hrv_results["Mean_PPI"]) + "ms", 0, 10)
        self.oled.text("Mean HR: " + str(hrv_results["Mean_HR"]) + "bpm", 0, 20)
        self.oled.text("SDNN: " + str(hrv_results["SDNN"]) + "ms", 0, 30)
        self.oled.text("RMSSD: " + str(hrv_results["RMSSD"]) + "ms", 0, 40)

        # Refresh display
        self.oled.show()

    # Kubios
    def draw_kubios_show_results(self):
        self.oled.fill(0)
        
        if len(measurer.CACHE_STORAGE_DYNAMIC) < 2:
            self.oled.text("Measurement failed", 0, 0)
            self.oled.show()
            return
            
        self.oled.text("Kubios Ready", 0, 0)
        self.oled.text("Analysis Done.", 0, 10)
        self.oled.show()
