import time
import measurer

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
            self.oled.text("-> Demo option 2", 0, 10)
        else:
            self.oled.text("   Demo option 2", 0, 10)
        if (current_selection == 2):
            self.oled.text("-> Demo option 3", 0, 20)
        else:
            self.oled.text("   Demo option 3", 0, 20)
        if (current_selection == 3):
            self.oled.text("-> Demo option 4", 0, 30)
        else:
            self.oled.text("   Demo option 4", 0, 30)
        if (current_selection == 4):
            self.oled.text("-> Settings", 0, 40)
        else:
            self.oled.text("   Settings", 0, 40)

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
        global heartbeat_first_met_all_criteria_timestamp
        print(len(measurer.PEAK_CACHE))
        self.oled.fill(0)
        self.oled.text(quality, 0, 10)
        if int(percentage_prepared) < 100:
            self.oled.text("Please wait...", 0, 30)
            self.oled.text("Calibrating", 0, 40)
            self.oled.text("Step 1. | " + str(int(percentage_prepared)) + "%", 0, 50)
        else:
            legal_beats_count = 0
            illegal_beats_count = 0
            last_beat_time = 0
            for i in range(len(measurer.PEAK_CACHE)):
                if i == 0:
                    legal_beats_count += 1
                else:
                    try:
                        time_diff = measurer.PEAK_CACHE[i].timestamp - measurer.PEAK_CACHE[i-1].timestamp
                        last_beat_time = measurer.PEAK_CACHE[i].timestamp
                        if time_diff > 300 and time_diff < 2000:
                            legal_beats_count += 1
                        else:
                            illegal_beats_count += 1
                    except IndexError:
                        pass
            ratio = legal_beats_count / (legal_beats_count + illegal_beats_count)
            print("Legal beats: " + str(legal_beats_count) + " Illegal beats: " + str(illegal_beats_count) + " Ratio: " + str(ratio))

            all_checks_passed = True

            if legal_beats_count < 3:
                self.oled.text("Not enough data.", 0, 40)
                all_checks_passed = False
                heartbeat_first_met_all_criteria_timestamp = 0
            
            elif (last_beat_time < time.ticks_ms() - 2500):
                self.oled.text("Data too old.", 0, 40)
                all_checks_passed = False
                heartbeat_first_met_all_criteria_timestamp = 0

            elif ratio < 0.7:
                self.oled.text("Bad read:" + str(int(ratio * 100)) + "%", 0, 40)
                all_checks_passed = False
                heartbeat_first_met_all_criteria_timestamp = 0
            else:
                self.oled.text("Almost there...", 0, 40)
                
            if all_checks_passed:
                if heartbeat_first_met_all_criteria_timestamp == 0:
                    heartbeat_first_met_all_criteria_timestamp = time.ticks_ms()
                delta = time.ticks_diff(time.ticks_ms(), heartbeat_first_met_all_criteria_timestamp)
                self.oled.text("Starting in " + str(5 - (delta // 1000)), 0, 50)

                if delta >= 5000:
                    return True

        self.oled.show()
        return False


    #ChatGPT paskaa, pitää rewrite myöhemmi
    def draw_measure(self, heart_rate):
        graph_height = self.oled.height - 10
        baseline = 10
        new_value = measurer.DYNAMIC_CACHE[-1]

        if getattr(self, 'last_peak_count', -1) != len(measurer.PEAK_CACHE):
            self.last_peak_count = len(measurer.PEAK_CACHE)
            if len(measurer.PEAK_CACHE) >= 2:
                total_time = measurer.PEAK_CACHE[-1].timestamp - measurer.PEAK_CACHE[0].timestamp
                self.BPM = (len(measurer.PEAK_CACHE)-1) * 60_000 // max(total_time, 1)
            else:
                self.BPM = 0

        if time.ticks_diff(time.ticks_ms(), getattr(self, 'last_text', 0)) > 200:
            self.oled.fill_rect(0, 0, self.oled.width, 10, 0)
            self.oled.text(f"HR: {self.BPM} BPM", 0, 0)
            self.last_text = time.ticks_ms()

        if not hasattr(self, 'min_val'):
            self.min_val = new_value
            self.max_val = new_value
            self.graph_buffer = [baseline + graph_height//2]*self.oled.width

        self.min_val = min(self.min_val, new_value)
        self.max_val = max(self.max_val, new_value)
        rng = max(self.max_val - self.min_val, 1)

        y = baseline + graph_height - ((new_value - self.min_val) * graph_height // rng)

        self.graph_buffer.pop(0)
        self.graph_buffer.append(y)

        self.oled.fill_rect(0, baseline, self.oled.width, graph_height, 0)
        for x, y_val in enumerate(self.graph_buffer):
            self.oled.pixel(x, y_val, 1)

        if time.ticks_diff(time.ticks_ms(), getattr(self, 'last_show', 0)) > 50:
            self.oled.show()
            self.last_show = time.ticks_ms()


   