from piotimer import Piotimer
from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C
from filefifo import Filefifo
import time
import GUI


#Input handler as globals for now, will fix later -Tom 
#-1 left, 0 no turn, 1 right, this is also a float that decays towards null.
INPUT_HANDLER_current_position = 0
#A decay from 1 or -1 to 0 takes 1000 ms.
INPUT_HANDLER_last_modified_time = time.ticks_ms()

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
adc = ADC(Pin(26))

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
            INPUT_HANDLER_current_position += 0.4
    else:
        if (INPUT_HANDLER_current_position > -1):
            INPUT_HANDLER_current_position -= 0.4
        

encoder_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_turn)

def __main__():
    gui = GUI.cGUI(oled)
    gui.draw_page_init()
    while True:
        gui.draw_main_menu(INPUT_HANDLER_current_position)
        print(str(INPUT_HANDLER_current_position))
        time.sleep(0.1)

    
    
if __name__ == "__main__":
    __main__()