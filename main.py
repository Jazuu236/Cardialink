binary_data = bytes([0x00])

import sys
from piotimer import Piotimer
from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C, Timer
from filefifo import Filefifo
import time
import GUI
import measurer
import panic
import framebuf
import menu_state

def show_logo(oled, width=128, height=64, duration=0):
    logo = framebuf.FrameBuffer(bytearray(binary_data), width, height, framebuf.MONO_VLSB)
    oled.fill(0)
    oled.blit(logo, 0, 0)
    oled.show()
    time.sleep(duration) #show logo x seconds


#GUI Page constants
CURRENT_PAGE = -1
TARGET_PAGE = -1 #
PAGE_MAINMENU = 0
PAGE_MEASURE_HR = 1
PAGE_HRV = 2
PAGE_HRV_SHOW_RESULTS = 3
PAGE_KUBIOS = 4
PAGE_KUBIOS_SHOW_RESULTS = 5
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

def pulse_timer_callback(timer, menu, measurer):
    if (menu.current_page != PAGE_MEASURE_HR and menu.current_page != PAGE_HRV and menu.current_page != PAGE_HRV_SHOW_RESULTS):
        measurer.clear_cache(measurer.CACHETYPE_DYNAMIC)
        measurer.clear_cache(measurer.CACHETYPE_200)
        measurer.clear_cache(measurer.CACHETYPE_BEATS)
        return
    raw_value = adc.read_u16()  #(0–65535)
    if ((raw_value < LEGAL_LOW) or (raw_value > LEGAL_HIGH)):
        return 
    
    #If we are in view result mode, we do not need to do anything else
    if (CURRENT_PAGE == PAGE_HRV_SHOW_RESULTS or CURRENT_PAGE == PAGE_KUBIOS_SHOW_RESULTS):
        return

    #Update both caches
    measurer.cache_update(measurer.CACHETYPE_200, raw_value)
    measurer.cache_update(measurer.CACHETYPE_DYNAMIC, raw_value)

    #Get the peak out of 200
    peak_value = measurer.cache_get_peak_value(measurer.CACHETYPE_200)
    if (peak_value == 0):
        return
    average_value = measurer.cache_get_average_value(measurer.CACHETYPE_200)
    difference = peak_value - average_value
    if (raw_value >= (average_value + difference * 0.6)):
        if (not measurer.PEAK_WAS_ALREADY_RECORDED):
            beat = measurer.cBeat(time.ticks_ms())
            measurer.add_to_beat_cache(beat)
            measurer.PEAK_WAS_ALREADY_RECORDED = True
        measurer.control_led(1)
    else:
        measurer.PEAK_WAS_ALREADY_RECORDED = False
        measurer.control_led(0)

    if (CURRENT_PAGE != PAGE_HRV and CURRENT_PAGE != PAGE_HRV_SHOW_RESULTS and CURRENT_PAGE != PAGE_KUBIOS and CURRENT_PAGE != PAGE_KUBIOS_SHOW_RESULTS):
        measurer.clear_cache(measurer.CACHETYPE_DYNAMIC)
    else:
        measurer.clear_cache(measurer.CACHETYPE_BEATS)

def __main__():
    
    # create OLED-object
    i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
    oled = SSD1306_I2C(128, 64, i2c)
   
    #show_logo(oled)

    #Create menu state object
    menu = menu_state.cMenuState()

    #Setup the interrupts

    encoder_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=lambda pin: encoder_turn(pin, menu.input_handler))

    timer = Timer()
    timer.init(freq=100, mode=Timer.PERIODIC, callback=lambda t: pulse_timer_callback(t, menu, measurer))

    gui = GUI.cGUI(oled)
    gui.draw_page_init()
    menu.current_page = PAGE_MAINMENU
    current_selection_index = 0

    i = 0

    while True: 
        i += 1
        call_time_start = time.ticks_ms()
        #Input handling
        if menu.input_handler.current_position >= 1:
            current_selection_index += 1
            if current_selection_index > 4:
                current_selection_index = 0
            menu.input_handler.current_position = 0
        elif menu.input_handler.current_position <= -1:
            current_selection_index -= 1
            if current_selection_index < 0:
                current_selection_index = 5
            menu.input_handler.current_position = 0

        if not menu.input_handler.button_has_been_released and button.value() == 1:
            menu.input_handler.button_has_been_released = True

        if panic.must_exit:
            print("###PANIC### " + panic.exit_reason)
            gracefully_exit()

        #------------------------------------
        #--------------PAGES-----------------
        #------------------------------------

        if menu.current_page == PAGE_MAINMENU:
            gui.draw_main_menu(current_selection_index, (menu.input_handler.current_position))

        elif menu.current_page == PAGE_MEASURE_HR: 
            gui.draw_measure_hr()

        elif menu.current_page == PAGE_HRV:
            if menu.hrv_measurement_started_ts > time.ticks_ms() - 30000:
                gui.draw_measure_hrv(menu.hrv_measurement_started_ts)
            else:
                menu.current_page = PAGE_HRV_SHOW_RESULTS

        elif menu.current_page == PAGE_HRV_SHOW_RESULTS:
            gui.draw_measure_hrv_show_results()
            
        elif CURRENT_PAGE == PAGE_KUBIOS:
            if FUCKASS_GLOBAL_HRV_MEASUREMENT_STARTED_TS > time.ticks_ms() - 30000:
                gui.draw_measure_kubios(FUCKASS_GLOBAL_HRV_MEASUREMENT_STARTED_TS)
            else:
                CURRENT_PAGE = PAGE_KUBIOS_SHOW_RESULTS

        elif CURRENT_PAGE == PAGE_KUBIOS_SHOW_RESULTS:
            gui.draw_kubios_show_results()

        #----------------------------------------
        #--------------END PAGES-----------------
        #----------------------------------------


        #If button pressed, select current option
        if button.value() == 0 and menu.input_handler.button_has_been_released:
            #MAINMENU
            if menu.current_page == PAGE_MAINMENU:
                menu.input_handler.button_has_been_released = False
                if current_selection_index == 0:
                    #Measure HR selected
                    menu.current_page = PAGE_MEASURE_HR
                elif current_selection_index == 1:
                    #Basic HRV selected
                    menu.hrv_measurement_started_ts = time.ticks_ms()
                    menu.current_page = PAGE_HRV
                elif current_selection_index == 4:
                    # Settings (EXIT) selected
                    gracefully_exit()
                    break

            # Page: PRESS TO START
            elif CURRENT_PAGE == PAGE_READY_TO_START:
                INPUT_HANDLER_button_has_been_released = False
                
                if TARGET_PAGE == PAGE_MEASURE_HR:
                    if hasattr(gui, "time_started"):
                        del gui.time_started
                    if hasattr(gui, "already_cleared"):
                        del gui.already_cleared
                
                elif TARGET_PAGE == PAGE_HRV or TARGET_PAGE == PAGE_KUBIOS:
                    FUCKASS_GLOBAL_HRV_MEASUREMENT_STARTED_TS = time.ticks_ms()
                
                CURRENT_PAGE = TARGET_PAGE
                
            #If we are in measure HR page, go back to main menu
            elif menu.current_page == PAGE_MEASURE_HR:
                menu.input_handler.button_has_been_released = False
                menu.current_page = PAGE_MAINMENU
                #Reset the time started for measure HR
                if hasattr(gui, "time_started"):
                    del gui.time_started
                if hasattr(gui, "already_cleared"):
                    del gui.already_cleared

        #Get the memory usage and print it
        if (i % 10) == 0:
            i = 0
            #Get the memory without 
            mem_usage = len(measurer.CACHE_STORAGE_200) + len(measurer.CACHE_STORAGE_DYNAMIC) + len(measurer.CACHE_STORAGE_BEATS)
            #print("Caches: " + str(mem_usage))
    
    
if __name__ == "__main__":
    __main__()
