import time
import panic
import peak_processing
import HRV


class cGUI:
    def __init__(self, oled):
        self.oled = oled

    def draw_page_init(self, Measurer):
        self.oled.fill(0)
        Measurer.control_led(0)
        self.oled.text("Initializing", 0, 0)
        self.oled.show()

    def draw_main_menu(self, current_selection, anim_pos):
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


        height = int(abs(-0.25) * (self.oled.height // 2)) 
        center_x = self.oled.width // 2
        base_y = int(self.oled.height - 1)

        if anim_pos > 0:
            # Arrow pointing DOWN
            top_y = base_y - height
            self.oled.line(center_x, base_y, center_x - 3, base_y - 3, 1)
            self.oled.line(center_x, base_y, center_x + 3, base_y - 3, 1)

        elif anim_pos < 0:
            # Arrow pointing UP
            top_y = base_y - height
            self.oled.line(center_x, top_y, center_x - 3, top_y + 3, 1)
            self.oled.line(center_x, top_y, center_x + 3, top_y + 3, 1)

        self.oled.show()

    def draw_ready_to_start(self, current_selection):
        self.oled.fill(0)

        # Confrim menu choice
        mode_text = "Start"
        if current_selection == 0:
            mode_text = "Start HR?"
        elif current_selection == 1:
            mode_text = "Start HRV?"
        elif current_selection == 2:
            mode_text = "Start Kubios?"
        
        x_pos = (128 - (len(mode_text) * 8)) // 2
        y_pos = 28
        self.oled.text(mode_text, x_pos, y_pos)
        self.oled.show()

    def draw_measure_hr(self, Measurer):
        #Display current read
        if len(Measurer.CACHE_STORAGE_BEATS) == 0:
            self.oled.fill(0)
            self.oled.text("Read: N/A", 0, 0)
            self.oled.show()
            return False
        num_beats = Measurer.get_beat_cache_length()
        time_since_first_beat = Measurer.CACHE_STORAGE_BEATS[0].age() if num_beats > 0 else 0

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

        if len(Measurer.CACHE_STORAGE_200) < 2:
            self.oled.text("Graph: N/A", 0, 10)
            self.oled.show()
            return False

        max_value = max(Measurer.CACHE_STORAGE_200)
        min_value = min(Measurer.CACHE_STORAGE_200)
        value_range = max_value - min_value

        if value_range == 0:
            self.oled.text("Graph: N/A (2)", 0, 10)
            self.oled.show()
            return False

        for i in range(len(Measurer.CACHE_STORAGE_200) - 1):
            val1 = Measurer.CACHE_STORAGE_200[i]
            val2 = Measurer.CACHE_STORAGE_200[i + 1]
            y1 = 10 + graph_height - int(((val1 - min_value) / value_range) * graph_height)
            y2 = 10 + graph_height - int(((val2 - min_value) / value_range) * graph_height)
            x1 = (i * graph_width) // len(Measurer.CACHE_STORAGE_200)
            x2 = ((i + 1) * graph_width) // len(Measurer.CACHE_STORAGE_200)
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


    def draw_measure_hrv_show_results(self, Measurer):
        self.oled.fill(0)
        #Calculate the treshold for peak detection
        if len(Measurer.CACHE_STORAGE_DYNAMIC) < 2:
            self.oled.text("Measurement failed", 0, 0)
            self.oled.text("Not enough data", 0, 10)
            self.oled.show()
            return
        avg_value = Measurer.cache_get_average_value(Measurer.CACHETYPE_DYNAMIC)
        threshold = avg_value + (Measurer.dynamic_cache_get_average_peak_value() - avg_value) * 0.6


        #Run PPI processing
        detected_peaks = peak_processing.detect_peaks(Measurer.CACHE_STORAGE_DYNAMIC, threshold, 10)

        ppi = []

        for i in range(1, len(detected_peaks)):
            ppi.append(detected_peaks[i][0] - detected_peaks[i-1][0])
        
        filtered_ppi = Measurer.ppi_filter_abnormalities(ppi, 33) #Filter all abnormalities greater than 33% deviation (pos <-> neg)

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
    def draw_kubios_show_results(self, Measurer):
        self.oled.fill(0)
        
        if len(Measurer.CACHE_STORAGE_DYNAMIC) < 2:
            self.oled.text("Measurement failed", 0, 0)
            self.oled.show()
            return
            
        self.oled.text("Kubios Ready", 0, 0)
        self.oled.text("Analysis Done.", 0, 10)
        self.oled.show()

    def draw_history_file(self, text):
        self.oled.fill(0)
        lines = text.split("#")
        for i, line in enumerate(lines):
            if i >= 6:
                break
            self.oled.text(line, 0, i * 10)
        self.oled.show()

