import sys
from piotimer import Piotimer
from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C, Timer
from filefifo import Filefifo
from visual_binary_data import startup_logo
import time
import GUI
import measurer
import panic
import framebuf
import menu_state
import history
import peak_processing
import kubios

def show_logo(oled, width=128, height=64, duration=0):
    logo = framebuf.FrameBuffer(bytearray(startup_logo), width, height, framebuf.MONO_VLSB)
    oled.fill(0)
    oled.blit(logo, 0, 0)
    oled.show()
    time.sleep(duration) #show logo x seconds


#GUI Page constants
PAGE_MAINMENU = 0
PAGE_MEASURE_HR = 1
PAGE_HRV = 2
PAGE_HRV_SHOW_RESULTS = 3
PAGE_KUBIOS = 4
PAGE_KUBIOS_SHOW_RESULTS = 5
PAGE_HISTORY_LIST = 6
PAGE_HISTORY_VIEW = 7
PAGE_READY_TO_START = 10


# ==========================
# Settings/components
# ==========================

# Display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

# LEDs
led1 = Pin(22, Pin.OUT)
led2 = Pin(21, Pin.OUT)
led3 = Pin(20, Pin.OUT)

# Rotary Encoder and Button
encoder_A = Pin(10, Pin.IN, Pin.PULL_UP)
encoder_B = Pin(11, Pin.IN, Pin.PULL_UP)
button = Pin(12, Pin.IN, Pin.PULL_UP)

# ADC
adc = ADC(Pin(27))

#Measurer settings
LEGAL_LOW = 30_000
LEGAL_HIGH = 40_000
DELAY_MS = 10


def encoder_turn(pin, input_handler):
    if encoder_B.value() != encoder_A.value():
        input_handler.current_position += 0.25
    else:
        input_handler.current_position -= 0.25

    if input_handler.current_position >= 1:
        input_handler.current_position = 1
    elif input_handler.current_position <= -1:
        input_handler.current_position = -1


def gracefully_exit():
    print("Shutting down...")
    oled.fill(0)
    oled.text("Shutdown", 0, 20)
    oled.show()
    led1.value(0)
    led2.value(0)
    led3.value(0)
    #Remove the IRQ
    encoder_A.irq(handler=None)
    #Shutdown the screen
    oled.poweroff()

def pulse_timer_callback(timer, Menu, Measurer):
    if (Menu.current_page != PAGE_MEASURE_HR and Menu.current_page != PAGE_HRV and Menu.current_page != PAGE_HRV_SHOW_RESULTS):
        Measurer.clear_cache(Measurer.CACHETYPE_DYNAMIC)
        Measurer.clear_cache(Measurer.CACHETYPE_200)
        Measurer.clear_cache(Measurer.CACHETYPE_BEATS)
        return
    raw_value = adc.read_u16()  #(0–65535)
    if ((raw_value < LEGAL_LOW) or (raw_value > LEGAL_HIGH)):
        return 
    
    #If we are in view result mode, we do not need to do anything else
    if (Menu.current_page == PAGE_HRV_SHOW_RESULTS or Menu.current_page == PAGE_KUBIOS_SHOW_RESULTS):
        return

    #Update both caches
    Measurer.cache_update(Measurer.CACHETYPE_200, raw_value)
    Measurer.cache_update(Measurer.CACHETYPE_DYNAMIC, raw_value)

    #Get the peak out of 200
    peak_value = Measurer.cache_get_peak_value(Measurer.CACHETYPE_200)
    if (peak_value == 0):
        return
    average_value = Measurer.cache_get_average_value(Measurer.CACHETYPE_200)
    difference = peak_value - average_value
    if (raw_value >= (average_value + difference * 0.6)):
        if (not Measurer.PEAK_WAS_ALREADY_RECORDED):
            beat = Measurer.cBeat(time.ticks_ms())
            Measurer.add_to_beat_cache(beat)
            Measurer.PEAK_WAS_ALREADY_RECORDED = True
        Measurer.control_led(1)
    else:
        Measurer.PEAK_WAS_ALREADY_RECORDED = False
        Measurer.control_led(0)

    if (Menu.current_page != PAGE_HRV and Menu.current_page != PAGE_HRV_SHOW_RESULTS and Menu.current_page != PAGE_KUBIOS and Menu.current_page != PAGE_KUBIOS_SHOW_RESULTS):
        Measurer.clear_cache(Measurer.CACHETYPE_DYNAMIC)
    else:
        Measurer.clear_cache(Measurer.CACHETYPE_BEATS)

def __main__():
    
    # create OLED-object
    i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
    oled = SSD1306_I2C(128, 64, i2c)
    
    # Show logo
    show_logo(oled, duration=2)
    
    #Create menu state object
    Menu = menu_state.cMenuState()

    #Create measurer object
    Measurer = measurer.cMeasurer()

    # Initialize Kubios Handler
    Kubios = kubios.KubiosHandler()
    kubios_sent = False
    
    #Setup the interrupts
    encoder_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=lambda pin: encoder_turn(pin, Menu.input_handler))

    timer = Timer()
    timer.init(freq=100, mode=Timer.PERIODIC, callback=lambda t: pulse_timer_callback(t, Menu, Measurer))

    gui = GUI.cGUI(oled)
    gui.draw_page_init(Measurer)

    Menu.current_page = PAGE_MAINMENU
    current_selection_index = 0
    TARGET_PAGE = -1 

    Menu.history_files = []
    Menu.selected_history_content = ""

    i = 0

    while True: 
        i += 1
        
        # INPUT LOGIC
        Kubios.check_messages()
        
        if Menu.current_page == PAGE_HISTORY_LIST:
            max_selection = len(Menu.history_files)
        elif Menu.current_page == PAGE_READY_TO_START:
            max_selection = 1 
        elif Menu.current_page == PAGE_HISTORY_VIEW:
            content = Menu.selected_history_content
            raw_lines = content.split("#")
            if len(raw_lines) < 2:
                raw_lines = content.split("\n")
            valid_lines = [l for l in raw_lines if l.replace("\n", "").strip()]
            max_selection = max(0, len(valid_lines) - 5)
        else:
            max_selection = 4
        
        # Encoder logic
        if Menu.input_handler.current_position >= 1:
            current_selection_index += 1
            if current_selection_index > max_selection:
                current_selection_index = 0 
            Menu.input_handler.current_position = 0
        elif Menu.input_handler.current_position <= -1:
            current_selection_index -= 1
            if current_selection_index < 0:
                current_selection_index = max_selection
            Menu.input_handler.current_position = 0

        if not Menu.input_handler.button_has_been_released and button.value() == 1:
            Menu.input_handler.button_has_been_released = True

        if panic.must_exit:
            print("###PANIC### " + panic.exit_reason)
            gracefully_exit()

        #------------------------------------
        #--------------PAGES-----------------
        #------------------------------------

        if Menu.current_page == PAGE_MAINMENU:
            gui.draw_main_menu(current_selection_index, (Menu.input_handler.current_position))

        elif Menu.current_page == PAGE_READY_TO_START:
            gui.draw_ready_to_start(current_selection_index, TARGET_PAGE)

        elif Menu.current_page == PAGE_MEASURE_HR: 
            gui.draw_measure_hr(Measurer)

        elif Menu.current_page == PAGE_HRV:
            if Menu.hrv_measurement_started_ts > time.ticks_ms() - 30000:
                gui.draw_measure_hrv(Menu.hrv_measurement_started_ts)
                kubios_sent = False
            else:
                if not kubios_sent:
                    ppi_list = peak_processing.extract_ppi(Measurer)
                    
                    if len(ppi_list) > 2:
                        try:
                            Kubios.send_analysis_request(ppi_list)
                        except Exception as e:
                            print("Failed to send Data:", e)
                    
                    kubios_sent = True
                Menu.current_page = PAGE_HRV_SHOW_RESULTS

        elif Menu.current_page == PAGE_HRV_SHOW_RESULTS:
            gui.draw_measure_hrv_show_results(Measurer)
            
        elif Menu.current_page == PAGE_KUBIOS:
            if Menu.hrv_measurement_started_ts > time.ticks_ms() - 30000:
                gui.draw_measure_kubios(Menu.hrv_measurement_started_ts)
                kubios_sent = False
            else:
                if not kubios_sent:
                    ppi_list = peak_processing.extract_ppi(Measurer)
                    
                    if len(ppi_list) > 2:
                        Kubios.send_analysis_request(ppi_list)
                    else:
                        print("Not enough valid peaks found")
                    
                    kubios_sent = True
                Menu.current_page = PAGE_KUBIOS_SHOW_RESULTS

        elif Menu.current_page == PAGE_KUBIOS_SHOW_RESULTS:
            Kubios.check_messages()
            gui.draw_kubios_show_results(Kubios)

        elif Menu.current_page == PAGE_HISTORY_LIST:
            gui.draw_history_list(current_selection_index, Menu.history_files)     

        elif Menu.current_page == PAGE_HISTORY_VIEW:
            gui.draw_history_file(Menu.selected_history_content, current_selection_index)


        #----------------------------------------
        #--------------END PAGES-----------------
        #----------------------------------------


        #If button pressed, select current option
        if button.value() == 0 and Menu.input_handler.button_has_been_released:
            
            # MAINMENU
            if Menu.current_page == PAGE_MAINMENU:
                Menu.input_handler.button_has_been_released = False
                
                if current_selection_index == 0:
                    TARGET_PAGE = PAGE_MEASURE_HR
                    Menu.current_page = PAGE_READY_TO_START
                    
                elif current_selection_index == 1:
                    TARGET_PAGE = PAGE_HRV
                    Menu.current_page = PAGE_READY_TO_START
                    
                elif current_selection_index == 2:
                    TARGET_PAGE = PAGE_KUBIOS
                    Menu.current_page = PAGE_READY_TO_START
                
                elif current_selection_index == 3:
                    Menu.history_files = history.get_history_files()
                    Menu.current_page = PAGE_HISTORY_LIST
                    Menu.input_handler.current_position = 0
                    current_selection_index = 0
                    
                elif current_selection_index == 4:
                    # Settings (EXIT) selected
                    gracefully_exit()
                    break

            # CONFIRM PAGE
            elif Menu.current_page == PAGE_READY_TO_START:
                Menu.input_handler.button_has_been_released = False
                
                if current_selection_index == 0:
                    if TARGET_PAGE == PAGE_MEASURE_HR:
                        if hasattr(gui, "time_started"):
                            del gui.time_started
                        if hasattr(gui, "already_cleared"):
                            del gui.already_cleared
                    
                    elif TARGET_PAGE == PAGE_HRV or TARGET_PAGE == PAGE_KUBIOS:
                        Menu.hrv_measurement_started_ts = time.ticks_ms()
                    
                    Menu.current_page = TARGET_PAGE
                    
                elif current_selection_index == 1:
                    Menu.current_page = PAGE_MAINMENU
                    current_selection_index = 0

            # HISTORY LIST PAGE
            elif Menu.current_page == PAGE_HISTORY_LIST:
                Menu.input_handler.button_has_been_released = False
                
                if current_selection_index == len(Menu.history_files):
                    Menu.current_page = PAGE_MAINMENU
                    
                elif len(Menu.history_files) > 0:
                    Menu.selected_history_content = history.get_history_content(current_selection_index)
                    Menu.current_page = PAGE_HISTORY_VIEW
                    current_selection_index = 0
                    Menu.input_handler.current_position = 0
                else:
                    Menu.current_page = PAGE_MAINMENU

            # HISTORY VIEW PAGE
            elif Menu.current_page == PAGE_HISTORY_VIEW:
                Menu.input_handler.button_has_been_released = False
                Menu.current_page = PAGE_HISTORY_LIST
                current_selection_index = 0

            # EXIT FROM HR MEASUREMENT
            elif Menu.current_page == PAGE_MEASURE_HR:
                Menu.input_handler.button_has_been_released = False
                Menu.current_page = PAGE_MAINMENU
                if hasattr(gui, "time_started"):
                    del gui.time_started
                if hasattr(gui, "already_cleared"):
                    del gui.already_cleared
            
            # EXIT FROM RESULTS
            elif (Menu.current_page == PAGE_HRV_SHOW_RESULTS or Menu.current_page == PAGE_KUBIOS_SHOW_RESULTS):
                Menu.input_handler.button_has_been_released = False
                Menu.current_page = PAGE_MAINMENU

        if (i % 10) == 0:
            i = 0

if __name__ == "__main__":
    __main__()
