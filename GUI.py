import time
import measurer
import panic

heartbeat_first_met_all_criteria_timestamp = 0

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
            self.oled.text("-> History", 0, 20)
        else:
            self.oled.text("   History", 0, 20)
        if (current_selection == 3):
            self.oled.text("-> Kubios", 0, 30)
        else:
            self.oled.text("   Kubios", 0, 30)
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

    def draw_measure_pre(self, quality, percentage_prepared):
        self.oled.fill(0)
        #Display current read
        if len(measurer.CACHE_STORAGE_200) == 0:
            self.oled.text("Read: N/A", 0, 0)
        else:
            self.oled.text("Read: " + str(measurer.CACHE_STORAGE_200[-1]), 0, 0)
        peak_value = measurer.cache_get_peak_value(measurer.CACHETYPE_200)
        if peak_value == 0:
            self.oled.text("Peak: N/A", 0, 10)
        else:
            rate_ratio = measurer.CACHE_STORAGE_200[-1] / peak_value
            self.oled.text("Peak: " + "{0:.2f}x".format(rate_ratio), 0, 10)
        difference = peak_value - measurer.cache_get_average_value(measurer.CACHETYPE_200)
        self.oled.text("Diff: " + str(int(difference)), 0, 20)
        if peak_value == 0:
            self.oled.text("R: N/A", 0, 30)
        else:
            dashes_to_display = int((measurer.CACHE_STORAGE_200[-1] - measurer.cache_get_average_value(measurer.CACHETYPE_200)) / (difference * 0.1))
            self.oled.text("R: " + ("-" * dashes_to_display), 0, 30)

        
        self.oled.show()
        return False


    #ChatGPT paskaa, pitää rewrite myöhemmi
    def draw_measure(self, heart_rate):
        graph_height = self.oled.height - 10
        baseline = 10

        window = measurer.DYNAMIC_CACHE[-5:]
        if len(window) < 2:
            return  # Need at least 2 points to draw lines

        # Determine vertical scaling
        min_val = min(window)
        max_val = max(window)
        rng = max(max_val - min_val, 1)

        # Clear graph area
        for x in range(self.oled.width):
            for y in range(baseline, baseline + graph_height):
                self.oled.pixel(x, y, 0)

        # Map window values into (x,y) positions
        points = []
        step = self.oled.width // (len(window) - 1)

        for i, val in enumerate(window):
            x = i * step
            y = baseline + graph_height - ((val - min_val) * graph_height // rng)
            points.append((x, y))

        # Draw lines between each pair of points
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            self.oled.line(x1, y1, x2, y2, 1)

        # Refresh display
        self.oled.show()
