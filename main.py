from piotimer import Piotimer
from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C
from filefifo import Filefifo
import time

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

def encoder_turn(pin):
    if encoder_B.value() != encoder_A.value():
        fifo.append("Right")
    else:
        fifo.append("Left")

encoder_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_turn)