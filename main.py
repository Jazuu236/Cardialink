import sys
from piotimer import Piotimer
from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C, Timer
from filefifo import Filefifo
import time
import GUI
import measurer
import panic


#GUI Page constants
CURRENT_PAGE = -1
PAGE_MAINMENU = 0
PAGE_MEASURE_HR = 1
PAGE_HRV = 2
PAGE_HRV_SHOW_RESULTS = 3

#Input handler as globals for now, will fix later -Tom 
#-1 left, 0 no turn, 1 right, this is also a float that decays towards null.
INPUT_HANDLER_current_position = 0
#A decay from 1 or -1 to 0 takes 1000 ms.
INPUT_HANDLER_last_modified_time = time.ticks_ms()
INPUT_HANDLER_button_has_been_released = True


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

PEAK_WAS_ALREADY_RECORDED = False

FUCKASS_GLOBAL_HRV_MEASUREMENT_STARTED_TS = 0


# FIFO
fifo =[]


# Encoder turn
def encoder_turn(pin):
    global INPUT_HANDLER_current_position
    global INPUT_HANDLER_last_modified_time

    #Decay logic, called on every turn
    time_diff = time.ticks_ms() - INPUT_HANDLER_last_modified_time
    decay_amount = (time_diff / 1000.0)

    if (decay_amount > 1):
        INPUT_HANDLER_current_position = 0
    elif (INPUT_HANDLER_current_position > 0):
        INPUT_HANDLER_current_position -= decay_amount
    elif (INPUT_HANDLER_current_position < 0):
        INPUT_HANDLER_current_position += decay_amount

    INPUT_HANDLER_last_modified_time = time.ticks_ms()

    if encoder_B.value() != encoder_A.value():
        if (INPUT_HANDLER_current_position < 1):
            INPUT_HANDLER_current_position += 0.35
    else:
        if (INPUT_HANDLER_current_position > -1):
            INPUT_HANDLER_current_position -= 0.35
        

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

def pulse_timer_callback(timer):
    global PEAK_WAS_ALREADY_RECORDED
    global measurer
    if (CURRENT_PAGE != PAGE_MEASURE_HR and CURRENT_PAGE != PAGE_HRV and CURRENT_PAGE != PAGE_HRV_SHOW_RESULTS):
        measurer.clear_cache(measurer.CACHETYPE_DYNAMIC)
        measurer.clear_cache(measurer.CACHETYPE_200)
        measurer.clear_cache(measurer.CACHETYPE_BEATS)
        return
    raw_value = adc.read_u16()  # 0–65535)
    if ((raw_value < LEGAL_LOW) or (raw_value > LEGAL_HIGH)):
        return 
    #print(str(raw_value) + ", ")
    #Update both caches

    #If we are in view result mode, we do not need to do anything else
    if (CURRENT_PAGE == PAGE_HRV_SHOW_RESULTS):
        return

    measurer.cache_update(measurer.CACHETYPE_200, raw_value)
    measurer.cache_update(measurer.CACHETYPE_DYNAMIC, raw_value)

    peak_value = measurer.cache_get_peak_value(measurer.CACHETYPE_200)
    if (peak_value == 0):
        return
    average_value = measurer.cache_get_average_value(measurer.CACHETYPE_200)
    difference = peak_value - average_value
    if (raw_value >= (average_value + difference * 0.6)):
        if (not PEAK_WAS_ALREADY_RECORDED):
            beat = measurer.cBeat(time.ticks_ms())
            measurer.add_to_beat_cache(beat)
            PEAK_WAS_ALREADY_RECORDED = True
        measurer.control_led(1)
    else:
        PEAK_WAS_ALREADY_RECORDED = False
        measurer.control_led(0)

    if (CURRENT_PAGE != PAGE_HRV and CURRENT_PAGE != PAGE_HRV_SHOW_RESULTS):
        #Clear dynamic cache as it's not used in this mode
        measurer.clear_cache(measurer.CACHETYPE_DYNAMIC)
    else:
        measurer.clear_cache(measurer.CACHETYPE_BEATS)

encoder_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_turn)

timer = Timer()
timer.init(freq=100, mode=Timer.PERIODIC, callback=pulse_timer_callback)


def __main__():
    global INPUT_HANDLER_current_position
    global INPUT_HANDLER_last_modified_time
    global INPUT_HANDLER_button_has_been_released
    global CURRENT_PAGE
    global FUCKASS_GLOBAL_HRV_MEASUREMENT_STARTED_TS

    gui = GUI.cGUI(oled)
    gui.draw_page_init()
    CURRENT_PAGE = PAGE_MAINMENU
    current_selection_index = 0

    i = 0

    while True: 
        i += 1
        call_time_start = time.ticks_ms()
        #Input handling
        if INPUT_HANDLER_current_position >= 1:
            current_selection_index += 1
            if current_selection_index > 5:
                current_selection_index = 0
            INPUT_HANDLER_current_position = 0
        elif INPUT_HANDLER_current_position <= -1:
            current_selection_index -= 1
            if current_selection_index < 0:
                current_selection_index = 5
            INPUT_HANDLER_current_position = 0

        if not INPUT_HANDLER_button_has_been_released and button.value() == 1:
            INPUT_HANDLER_button_has_been_released = True

        if panic.must_exit:
            print("###PANIC### " + panic.exit_reason)
            gracefully_exit()

        #------------------------------------
        #--------------PAGES-----------------
        #------------------------------------


        if CURRENT_PAGE == PAGE_MAINMENU:
            gui.draw_main_menu(current_selection_index, abs(INPUT_HANDLER_current_position), INPUT_HANDLER_last_modified_time)

        elif CURRENT_PAGE == PAGE_MEASURE_HR: 
            gui.draw_measure_hr()

        elif CURRENT_PAGE == PAGE_HRV:
            if FUCKASS_GLOBAL_HRV_MEASUREMENT_STARTED_TS > time.ticks_ms() - 30000:
                gui.draw_measure_hrv(FUCKASS_GLOBAL_HRV_MEASUREMENT_STARTED_TS)
            else:
                CURRENT_PAGE = PAGE_HRV_SHOW_RESULTS

        elif CURRENT_PAGE == PAGE_HRV_SHOW_RESULTS:
            gui.draw_measure_hrv_show_results()

        #----------------------------------------
        #--------------END PAGES-----------------
        #----------------------------------------


        #If button pressed, select current option
        if button.value() == 0 and INPUT_HANDLER_button_has_been_released:
            #MAINMENU
            if CURRENT_PAGE == PAGE_MAINMENU:
                INPUT_HANDLER_button_has_been_released = False
                if current_selection_index == 0:
                    #Measure HR selected
                    CURRENT_PAGE = PAGE_MEASURE_HR
                elif current_selection_index == 1:
                    #Basic HRV selected
                    FUCKASS_GLOBAL_HRV_MEASUREMENT_STARTED_TS = time.ticks_ms()
                    CURRENT_PAGE = PAGE_HRV
                elif current_selection_index == 4:
                    #Settings (EXIT) selected
                    gracefully_exit()
                    break
                
            #If we are in measure HR page, go back to main menu
            elif CURRENT_PAGE == PAGE_MEASURE_HR:
                INPUT_HANDLER_button_has_been_released = False
                CURRENT_PAGE = PAGE_MAINMENU

        #Get the memory usage and print it
        if (i % 10) == 0:
            i = 0
            #Get the memory without 
            mem_usage = len(measurer.CACHE_STORAGE_200) + len(measurer.CACHE_STORAGE_DYNAMIC) + len(measurer.CACHE_STORAGE_BEATS)
            #print("Caches: " + str(mem_usage))
    
    
if __name__ == "__main__":
    __main__()