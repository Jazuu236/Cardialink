import time
import peak_processing
import HRV

class cGUI:
    def __init__(self, oled):
        """
        Initialize the GUI handler with the OLED display object.
        """
        self.oled = oled

    def draw_page_init(self, Measurer):
        """
        Draw the initialization screen and turn off the sensor LED.
        """
        self.oled.fill(0)
        Measurer.control_led(0)
        self.oled.text("Initializing", 0, 0)
        self.oled.show()

    def draw_main_menu(self, current_selection, anim_pos):
        """
        Render the main menu items and the animated selection arrow.
        
        Args:
            current_selection (int): Index of the selected menu item.
            anim_pos (float): Position for the animated arrow.
        """
        self.oled.fill(0)
        
        # Draw menu items with selection indicator
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
            self.oled.text("-> Turn OFF", 0, 40)
        else:
            self.oled.text("   Turn OFF", 0, 40)

        # Draw the animated arrow at the bottom
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

    def draw_ready_to_start(self, current_selection, target_page):
        """
        Draw the confirmation page before starting a measurement.
        Allows the user to Start or Go Back.
        """
        self.oled.fill(0)

        mode_text = "Press to Start"
        if target_page == 1: 
            mode_text = "Start HR?"
        elif target_page == 2:
            mode_text = "Start HRV?"
        elif target_page == 4:
            mode_text = "Start Kubios?"
        
        # Center the title text
        x_pos = (128 - (len(mode_text) * 8)) // 2
        y_pos = 10
        self.oled.text(mode_text, x_pos, y_pos)
        
        # Show selection options (Start / Back)
        if current_selection == 0:
            self.oled.text("-> START", 20, 40)
            self.oled.text("   BACK", 20, 50)
        else:
            self.oled.text("   START", 20, 40)
            self.oled.text("-> BACK", 20, 50)

        self.oled.show()

    def draw_measure_hr(self, Measurer):
        """
        Display the real-time Heart Rate (BPM) and a raw signal graph.
        """
        # Display current read
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
        
        # Clear the top area for text
        self.oled.fill_rect(0, 0, self.oled.width, 10, 0)

        if not hasattr(self, "already_cleared"):
            self.already_cleared = True
            self.oled.fill(0)
            self.oled.text("Preparing...", 0, 0)
            self.oled.show()
            return False
        
        if not hasattr(self, "time_started"):
            self.time_started = time.ticks_ms()

        # Show loading dots for the first 5 seconds, then show BPM
        if (self.time_started + 5000) > time.ticks_ms():
            dots = ((time.ticks_ms() // 500) % 4)
            self.oled.text("BPM: " + dots * ".", 0, 0)
            self.oled.show()
        else:
            bpm = (num_beats * 60000) / time_since_first_beat
            self.oled.text("BPM: " + "{0:.1f}".format(bpm), 0, 0)

        # Draw the signal graph
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
        """
        Show the countdown timer for the HRV measurement process.
        """
        self.oled.fill(0)

        time_remaining = 30_000 - time.ticks_diff(time.ticks_ms(), start_ts)

        self.oled.text("Measuring HRV...", 0, 0)
        self.oled.text("Please wait " + str(max(time_remaining // 1000, 0)) + "s", 0, 10)

        if (time_remaining < 0):
            self.oled.fill(0)

        self.oled.show()

    def draw_measure_kubios(self, start_ts):
        """
        Show the countdown timer for the Kubios analysis process.
        """
        self.oled.fill(0)

        time_remaining = 30_000 - time.ticks_diff(time.ticks_ms(), start_ts)

        self.oled.text("Kubios Analysis", 0, 0)
        self.oled.text("Measuring...", 0, 10)
        self.oled.text("Wait: " + str(max(time_remaining // 1000, 0)) + "s", 0, 30)

        if (time_remaining < 0):
            self.oled.fill(0)

        self.oled.show()


    def draw_measure_hrv_show_results(self, Measurer):
        """
        Calculate PPI/HRV metrics from collected data and display the results.
        """
        self.oled.fill(0)
        
        # Calculate the threshold for peak detection
        if len(Measurer.CACHE_STORAGE_DYNAMIC) < 2:
            self.oled.text("Measurement failed", 0, 0)
            self.oled.text("Not enough data", 0, 10)
            self.oled.show()
            return
            
        avg_value = Measurer.cache_get_average_value(Measurer.CACHETYPE_DYNAMIC)
        threshold = avg_value + (Measurer.dynamic_cache_get_average_peak_value() - avg_value) * 0.6

        # Run PPI (Peak-to-Peak Interval) processing
        detected_peaks = peak_processing.detect_peaks(Measurer.CACHE_STORAGE_DYNAMIC, threshold, 10)

        ppi = []
        for i in range(1, len(detected_peaks)):
            ppi.append(detected_peaks[i][0] - detected_peaks[i-1][0])
        
        # Filter all abnormalities greater than 33% deviation
        filtered_ppi = Measurer.ppi_filter_abnormalities(ppi, 33) 

        hrv_results = HRV.hrv_analysis(filtered_ppi)
        
        # Display results
        self.oled.text("HRV Results:", 0, 0)
        self.oled.text("Mean PPI: " + str(hrv_results["Mean_PPI"]) + "ms", 0, 10)
        self.oled.text("Mean HR: " + str(hrv_results["Mean_HR"]) + "bpm", 0, 20)
        self.oled.text("SDNN: " + str(hrv_results["SDNN"]) + "ms", 0, 30)
        self.oled.text("RMSSD: " + str(hrv_results["RMSSD"]) + "ms", 0, 40)

        self.oled.show()

    def draw_kubios_show_results(self, kubios_handler):
        """
        Display Kubios results or a loading screen.
        """
        self.oled.fill(0)

        # 1. Check if we are still waiting for data
        if kubios_handler.waiting_for_response:
            dots = ((time.ticks_ms() // 500) % 4)
            self.oled.text("Sending Data" + dots * ".", 0, 0)
            self.oled.text("Analysing...", 0, 20)
            self.oled.show()
            return

        # 2. Check if we have results
        results = kubios_handler.analysis_result
        if results is None:
            self.oled.text("Measurement Fail", 0, 0)
            self.oled.text("Or WiFi Error", 0, 10)
            self.oled.text("Try again", 0, 30)
            self.oled.show()
            return

        # 3. Display the Kubios Data
        self.oled.text("Kubios Results:", 0, 0)

        self.oled.text("HR:{:.0f} bpm".format(results.get("mean_hr_bpm", 0)), 0, 10)
        self.oled.text("PNS:{:.1f} SNS:{:.1f}".format(results.get("pns_index", 0), results.get("sns_index", 0)), 0, 20)
        self.oled.text("RMSSD:{:.0f}".format(results.get("rmssd_ms", 0)), 0, 30)
        self.oled.text("SDNN:{:.1f}".format(results.get("sdnn_ms", 0)), 0, 40)
        self.oled.text("Stress:{:.1f}".format(results.get("stress_index", 0)), 0, 50)
        
        self.oled.show()

    def draw_history_list(self, current_selection, history_files):
        """
        Render a scrollable list of saved history files with formatted timestamps.
        """
        self.oled.fill(0)
        self.oled.text("Select File:", 0, 0)
        
        display_list = history_files + ["Back"]
        
        # Calculate scroll offset
        start_index = 0
        if current_selection >= 4:
            start_index = current_selection - 4
            
        # Draw up to 5 items on the screen
        for i in range(5):
            item_index = start_index + i
            if item_index >= len(display_list):
                break
            
            item = display_list[item_index]
            y_pos = 10 + (i * 10)
            
            if item == "Back":
                display_text = "Back"
            else:
                # Parse filename to display readable date/time
                filename = item.split("/")[-1]
                clean_name = filename.replace("kubios_", "").replace(".txt", "")
                
                try:
                    parts = clean_name.split("_") 
                    if len(parts) >= 2:
                        date_part = parts[0].split("-") # [YYYY, MM, DD]
                        time_part = parts[1].split("-") # [HH, MM, SS]
                        
                        # Format: HH:MM DD.MM
                        display_text = "{}:{} {}.{}".format(time_part[0], time_part[1], date_part[2], date_part[1])
                    else:
                        display_text = clean_name[:14]
                except:
                    display_text = clean_name[:14]

            if item_index == current_selection:
                self.oled.text("-> " + display_text, 0, y_pos)
            else:
                self.oled.text("   " + display_text, 0, y_pos)
                
        self.oled.show()

    def draw_analyzing(self):
        """
        Show a transition screen while calculating local HRV results.
        """
        self.oled.fill(0)
        self.oled.text("Basic HRV", 0, 0)
        self.oled.text("Measuring...", 0, 25)
        self.oled.show()

    def draw_history_file(self, text, scroll_offset=0):
        """
        Display the content of a selected history file with scrolling.
        """
        self.oled.fill(0)
        
        if not text:
            self.oled.text("Empty / Error", 0, 0)
            self.oled.show()
            return

        # Split text into clean lines first
        raw_lines = text.split("#")
        if len(raw_lines) < 2:
            raw_lines = text.split("\n")
            
        lines = []
        for line in raw_lines:
            clean_line = line.replace("\n", "").strip()
            if len(clean_line) > 0:
                lines.append(clean_line)

        # Draw 6 lines starting from scroll_offset
        max_lines_on_screen = 6
        
        for i in range(max_lines_on_screen):
            line_index = scroll_offset + i
            
            # Stop if we run out of lines
            if line_index >= len(lines):
                break
                
            self.oled.text(lines[line_index], 0, i * 10)
            
        self.oled.show()
