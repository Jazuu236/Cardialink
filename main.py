from piotimer import Piotimer
from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C, Timer
from filefifo import Filefifo
import time
import GUI
import measurer


#GUI Page constants
CURRENT_PAGE = -1
PAGE_MAINMENU = 0
PAGE_MEASURE_PRE = 1
PAGE_MEASURE = 2

#Input handler as globals for now, will fix later -Tom 
#-1 left, 0 no turn, 1 right, this is also a float that decays towards null.
INPUT_HANDLER_current_position = 0
#A decay from 1 or -1 to 0 takes 1000 ms.
INPUT_HANDLER_last_modified_time = time.ticks_ms()
INPUT_HANDLER_button_has_been_released = True

#Placeholder interrupt variables for pulse measurements
PULSE_quality= "N/A"
PULSE_percentage_prepared = 0

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
    if (CURRENT_PAGE != PAGE_MEASURE_PRE and CURRENT_PAGE != PAGE_MEASURE):
        return
    global PULSE_quality
    global PULSE_percentage_prepared
    global measurer
    raw_value = adc.read_u16()  # Read 16-bit ADC value (0–65535)
    if ((raw_value < LEGAL_LOW) or (raw_value > LEGAL_HIGH)):
        return 
    avg_value = measurer.cache_update(raw_value)
    #("val: " + str(raw_value) + "avg:" + str(avg_value) + "len:" + str(len(measurer.DYNAMIC_CACHE)) + "tresh:" + str((measurer.cache_get_peak_value()))+ " R: " + str(measurer.cache_get_peak_ratio()))
    PULSE_quality = measurer.get_reading_quality(measurer.cache_get_peak_ratio())
    PULSE_percentage_prepared = int(measurer.get_percent_prepared())
    if ((raw_value > (measurer.cache_get_peak_value()) * 0.99)):
        measurer.control_led(1)
        peak = measurer.cBeat(time.ticks_ms(), raw_value)

        if PEAK_WAS_ALREADY_RECORDED:
            return
        measurer.add_to_peak_cache(peak)
        PEAK_WAS_ALREADY_RECORDED = True
    else:
        measurer.control_led(0)
        PEAK_WAS_ALREADY_RECORDED = False
    

encoder_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_turn)

timer = Timer()
timer.init(freq=100, mode=Timer.PERIODIC, callback=pulse_timer_callback)


def __main__():
    global INPUT_HANDLER_current_position
    global INPUT_HANDLER_last_modified_time
    global INPUT_HANDLER_button_has_been_released
    global CURRENT_PAGE
    global PULSE_quality
    global PULSE_percentage_prepared

    gui = GUI.cGUI(oled)
    gui.draw_page_init()
    CURRENT_PAGE = PAGE_MAINMENU
    current_selection_index = 0

    while True: 
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

        #------------------------------------
        #--------------PAGES-----------------
        #------------------------------------


        if CURRENT_PAGE == PAGE_MAINMENU:
            gui.draw_main_menu(current_selection_index, abs(INPUT_HANDLER_current_position), INPUT_HANDLER_last_modified_time)

        elif CURRENT_PAGE == PAGE_MEASURE_PRE: 
            ready_to_measure = gui.draw_measure_pre(PULSE_quality, PULSE_percentage_prepared)
            if (ready_to_measure):
                CURRENT_PAGE = PAGE_MEASURE

        elif CURRENT_PAGE == PAGE_MEASURE:
            gui.draw_measure(60)
            print("Time to draw measure page: " + str(time.ticks_diff(time.ticks_ms(), call_time_start)) + " ms")


        #----------------------------------------
        #--------------END PAGES-----------------
        #----------------------------------------


        #If button pressed, select current option
        if button.value() == 0 and INPUT_HANDLER_button_has_been_released:
            INPUT_HANDLER_button_has_been_released = False
            if current_selection_index == 0:
                #Measure HR selected
                CURRENT_PAGE = PAGE_MEASURE_PRE
            elif current_selection_index == 4:
                #Settings (EXIT) selected
                gracefully_exit()
                break
    
    
if __name__ == "__main__":
    __main__()