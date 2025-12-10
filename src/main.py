import sys
from piotimer import Piotimer
from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C, Timer
from filefifo import Filefifo
from visual_binary_data import startup_logo
from config import connect_wlan
import time
import GUI
import measurer
import framebuf
import menu_state
import history
import peak_processing
import kubios

# -------------------------
# Logo
# -------------------------
def show_logo(oled, width=128, height=64):
    logo = framebuf.FrameBuffer(bytearray(startup_logo), width, height, framebuf.MONO_VLSB)
    oled.fill(0)
    oled.blit(logo, 0, 0)
    oled.show()

# -------------------------
# GUI Page constants
# -------------------------
PAGE_MAINMENU = 0
PAGE_MEASURE_HR = 1
PAGE_HRV = 2
PAGE_HRV_SHOW_RESULTS = 3
PAGE_KUBIOS = 4
PAGE_KUBIOS_SHOW_RESULTS = 5
PAGE_HISTORY_LIST = 6
PAGE_HISTORY_VIEW = 7
PAGE_READY_TO_START = 10

# -------------------------
# Hardware settings
# -------------------------
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

led1 = Pin(22, Pin.OUT)
led2 = Pin(21, Pin.OUT)
led3 = Pin(20, Pin.OUT)

encoder_A = Pin(10, Pin.IN, Pin.PULL_UP)
encoder_B = Pin(11, Pin.IN, Pin.PULL_UP)
button = Pin(12, Pin.IN, Pin.PULL_UP)

adc = ADC(Pin(27))

LEGAL_LOW = 30_000
LEGAL_HIGH = 40_000
DELAY_MS = 10

# -------------------------
# Encoder helper
# -------------------------
def encoder_turn(pin, input_handler):
    if encoder_B.value() != encoder_A.value():
        input_handler.current_position += 0.25
    else:
        input_handler.current_position -= 0.25

    if input_handler.current_position >= 1:
        input_handler.current_position = 1
    elif input_handler.current_position <= -1:
        input_handler.current_position = -1

# -------------------------
# Exit gracefully
# -------------------------
def gracefully_exit():
    print("Shutting down...")
    oled.fill(0)
    oled.text("Shutdown", 0, 20)
    oled.show()
    led1.value(0)
    led2.value(0)
    led3.value(0)
    encoder_A.irq(handler=None)
    oled.poweroff()

# -------------------------
# Extract PPI for Kubios
# -------------------------
def extract_ppi_for_kubios(Measurer):
    if len(Measurer.CACHE_STORAGE_DYNAMIC) < 2:
        return []

    avg_value = Measurer.cache_get_average_value(Measurer.CACHETYPE_DYNAMIC)
    threshold = avg_value + (Measurer.dynamic_cache_get_average_peak_value() - avg_value) * 0.6

    detected_peaks = peak_processing.detect_peaks(Measurer.CACHE_STORAGE_DYNAMIC, threshold, 10)

    ppi = []
    for i in range(1, len(detected_peaks)):
        ppi.append(detected_peaks[i][0] - detected_peaks[i-1][0])

    filtered_ppi = Measurer.ppi_filter_abnormalities(ppi, 33)
    return filtered_ppi

# -------------------------
# Pulse Timer callback
# -------------------------
def pulse_timer_callback(timer, Menu, Measurer):

    if (Measurer.temp_restrict_updates):
        print("UPD:REST")
        return


    if Menu.current_page not in (PAGE_MEASURE_HR, PAGE_HRV, PAGE_HRV_SHOW_RESULTS, PAGE_KUBIOS, PAGE_KUBIOS_SHOW_RESULTS):
        Measurer.clear_cache(Measurer.CACHETYPE_DYNAMIC)
        Measurer.clear_cache(Measurer.CACHETYPE_200)
        Measurer.clear_cache(Measurer.CACHETYPE_BEATS)
        return

    raw_value = adc.read_u16()
    if raw_value < LEGAL_LOW or raw_value > LEGAL_HIGH:
        return

    if Menu.current_page in (PAGE_HRV_SHOW_RESULTS, PAGE_KUBIOS_SHOW_RESULTS):
        return

    Measurer.cache_update(Measurer.CACHETYPE_200, raw_value)
    Measurer.cache_update(Measurer.CACHETYPE_DYNAMIC, raw_value)

    peak_value = Measurer.cache_get_peak_value(Measurer.CACHETYPE_200)
    if peak_value == 0:
        return
    average_value = Measurer.cache_get_average_value(Measurer.CACHETYPE_200)
    difference = peak_value - average_value

    if raw_value >= (average_value + difference * 0.6):
        if not Measurer.PEAK_WAS_ALREADY_RECORDED:
            beat = Measurer.cBeat(time.ticks_ms())
            Measurer.add_to_beat_cache(beat)
            Measurer.PEAK_WAS_ALREADY_RECORDED = True
        Measurer.control_led(1)
    else:
        Measurer.PEAK_WAS_ALREADY_RECORDED = False
        Measurer.control_led(0)

    # Clear caches based on page
    if Menu.current_page in (PAGE_HRV, PAGE_HRV_SHOW_RESULTS, PAGE_KUBIOS, PAGE_KUBIOS_SHOW_RESULTS):
        Measurer.clear_cache(Measurer.CACHETYPE_BEATS)

    #Limit dynamic cache to 1000 when measuring HR
    if Menu.current_page == PAGE_MEASURE_HR:
        Measurer.clear_cache_with_limit(Measurer.CACHETYPE_DYNAMIC, 1000)

# -------------------------
# Main
# -------------------------
def __main__():
    
    show_logo(oled)
    start_time = time.ticks_ms()

    try:
        connect_wlan() 
    except Exception as e:
        print("Network init failed:", e)
    
    Menu = menu_state.cMenuState()
    Measurer = measurer.cMeasurer()
    Kubios = kubios.KubiosHandler()
    kubios_sent = False

    encoder_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=lambda pin: encoder_turn(pin, Menu.input_handler))
    timer = Timer()
    timer.init(freq=100, mode=Timer.PERIODIC, callback=lambda t: pulse_timer_callback(t, Menu, Measurer))

    while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
        time.sleep(0.1)

    gui = GUI.cGUI(oled)
    Measurer.control_led(0) 

    Menu.current_page = PAGE_MAINMENU
    current_selection_index = 0
    TARGET_PAGE = -1
    Menu.history_files = []
    Menu.selected_history_content = ""
    i = 0
    
    while True:
        i += 1
        Kubios.check_messages()

        # Max selection logic
        if Menu.current_page == PAGE_HISTORY_LIST:
            max_selection = len(Menu.history_files)
        elif Menu.current_page == PAGE_READY_TO_START:
            max_selection = 1
        elif Menu.current_page == PAGE_HISTORY_VIEW:
            content = Menu.selected_history_content
            raw_lines = content.split("#") if len(content.split("#")) > 1 else content.split("\n")
            valid_lines = [l for l in raw_lines if l.strip()]
            max_selection = max(0, len(valid_lines) - 5)
        else:
            max_selection = 4

        # Encoder navigation
        if Menu.input_handler.current_position >= 1:
            current_selection_index = (current_selection_index + 1) % (max_selection + 1)
            Menu.input_handler.current_position = 0
        elif Menu.input_handler.current_position <= -1:
            current_selection_index = (current_selection_index - 1) % (max_selection + 1)
            Menu.input_handler.current_position = 0

        if not Menu.input_handler.button_has_been_released and button.value() == 1:
            Menu.input_handler.button_has_been_released = True

        # -------------------
        # Pages
        # -------------------
        if Menu.current_page == PAGE_MAINMENU:
            gui.draw_main_menu(current_selection_index, Menu.input_handler.current_position)
        elif Menu.current_page == PAGE_READY_TO_START:
            gui.draw_ready_to_start(current_selection_index, TARGET_PAGE)
        elif Menu.current_page == PAGE_MEASURE_HR:
            gui.draw_measure_hr(Measurer)
        elif Menu.current_page == PAGE_HRV:
            if Menu.hrv_measurement_started_ts > time.ticks_ms() - 30000:
                gui.draw_measure_hrv(Menu.hrv_measurement_started_ts)
                kubios_sent = False
            else:
                gui.draw_analyzing()
                if not kubios_sent:
                    Measurer.temp_restrict_updates = True
                    ppi_list = extract_ppi_for_kubios(Measurer)
                    if len(ppi_list) > 2:
                        Kubios.send_analysis_request(ppi_list)
                    kubios_sent = True
                    Measurer.temp_restrict_updates = False
                Menu.current_page = PAGE_HRV_SHOW_RESULTS
                
        elif Menu.current_page == PAGE_HRV_SHOW_RESULTS:
            gui.draw_measure_hrv_show_results(Measurer)
        elif Menu.current_page == PAGE_KUBIOS:
            if Menu.hrv_measurement_started_ts > time.ticks_ms() - 30000:
                gui.draw_measure_kubios(Menu.hrv_measurement_started_ts, Measurer)
                kubios_sent = False
            else:
                if not kubios_sent:
                    Measurer.temp_restrict_updates = True
                    ppi_list = extract_ppi_for_kubios(Measurer)
                    if len(ppi_list) > 2:
                        Kubios.send_analysis_request(ppi_list)
                    else:
                        print("Not enough valid peaks found (Kubios)")
                    kubios_sent = True
                    Measurer.temp_restrict_updates = False
                Menu.current_page = PAGE_KUBIOS_SHOW_RESULTS
        elif Menu.current_page == PAGE_KUBIOS_SHOW_RESULTS:
            Kubios.check_messages()
            gui.draw_kubios_show_results(Kubios)
        elif Menu.current_page == PAGE_HISTORY_LIST:
            gui.draw_history_list(current_selection_index, Menu.history_files)
        elif Menu.current_page == PAGE_HISTORY_VIEW:
            gui.draw_history_file(Menu.selected_history_content, current_selection_index)

        # -------------------
        # Button press logic
        # -------------------
        if button.value() == 0 and Menu.input_handler.button_has_been_released:
            Menu.input_handler.button_has_been_released = False
            # MAIN MENU selections
            if Menu.current_page == PAGE_MAINMENU:
                if current_selection_index == 0:
                    TARGET_PAGE = PAGE_MEASURE_HR
                elif current_selection_index == 1:
                    TARGET_PAGE = PAGE_HRV
                elif current_selection_index == 2:
                    TARGET_PAGE = PAGE_KUBIOS
                elif current_selection_index == 3:
                    Menu.history_files = history.get_history_files()
                    Menu.current_page = PAGE_HISTORY_LIST
                    Menu.input_handler.current_position = 0
                    current_selection_index = 0
                    continue
                elif current_selection_index == 4:
                    gracefully_exit()
                    break
                Menu.current_page = PAGE_READY_TO_START

            # CONFIRM PAGE
            elif Menu.current_page == PAGE_READY_TO_START:
                if current_selection_index == 0:
                    if TARGET_PAGE in (PAGE_HRV, PAGE_KUBIOS):
                        Menu.hrv_measurement_started_ts = time.ticks_ms()
                    Menu.current_page = TARGET_PAGE
                else:
                    Menu.current_page = PAGE_MAINMENU
                    current_selection_index = 0

            # HISTORY LIST
            elif Menu.current_page == PAGE_HISTORY_LIST:
                if current_selection_index == len(Menu.history_files):
                    Menu.current_page = PAGE_MAINMENU
                else:
                    Menu.selected_history_content = history.get_history_content(current_selection_index)
                    Menu.current_page = PAGE_HISTORY_VIEW
                    current_selection_index = 0
                    Menu.input_handler.current_position = 0

            # HISTORY VIEW
            elif Menu.current_page == PAGE_HISTORY_VIEW:
                Menu.current_page = PAGE_HISTORY_LIST
                current_selection_index = 0

            # EXIT FROM HR MEASUREMENTS
            elif Menu.current_page == PAGE_MEASURE_HR:
                Menu.current_page = PAGE_MAINMENU
                if hasattr(gui, "time_started"):
                    del gui.time_started
                if hasattr(gui, "already_cleared"):
                    del gui.already_cleared

            # EXIT FROM RESULTS
            elif Menu.current_page in (PAGE_HRV_SHOW_RESULTS, PAGE_KUBIOS_SHOW_RESULTS):
                Menu.current_page = PAGE_MAINMENU

        if (i % 10) == 0:
            i = 0
            print("Cache sizes: DYN={}, 200={}, BEATS={}".format(
                len(Measurer.CACHE_STORAGE_DYNAMIC),
                len(Measurer.CACHE_STORAGE_200),
                len(Measurer.CACHE_STORAGE_BEATS)
            ))

if __name__ == "__main__":
    __main__()
