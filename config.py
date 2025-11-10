# Imports
from machine import ADC, Pin, I2C
from ssd1306 import SSD1306_I2C
from filefifo import Filefifo
import time

# Display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

# Leds
led1 = Pin(22, Pin.OUT)
led2 = Pin(21, Pin.OUT)
led3 = Pin(20, Pin.OUT)

# Rotary and button
encoder_A = Pin(11, Pin.IN, Pin.PULL_UP)
encoder_B = Pin(10, Pin.IN, Pin.PULL_UP)
button = Pin(12, Pin.IN, Pin.PULL_UP)

# Fifo
fifo = []

# Rotary def
def Rotary(pin):
    a = encoder_A.value()
    b = encoder_B.value()
    if a == b:
        fifo.append("LEFT")
    else:
        fifo.append("RIGTH")
        
encoder_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_turn)

