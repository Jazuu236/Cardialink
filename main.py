from machine import ADC, Pin, I2C
from ssd1306 import SSD1306_I2C
from filefifo import Filefifo
import time

# ==========================
# Settings
# ==========================

# OLED
PIN_I2C_SCL = 15
PIN_I2C_SDA = 14
I2C_FREQ = 400000
OLED_WIDTH = 128
OLED_HEIGHT = 64

# LEDs
PIN_LED1 = 22
PIN_LED2 = 21
PIN_LED3 = 20

# Rotary Encoder
PIN_ENCODER_A = 10
PIN_ENCODER_B = 11
PIN_BUTTON = 12

# ADC
PIN_ADC0 = 26
PIN_ADC1 = 2

# FIFO buffer size
FIFO_MAX_SIZE = 50

# ==========================
# Components
# ==========================

# Display
i2c = I2C(1, scl=Pin(PIN_I2C_SCL), sda=Pin(PIN_I2C_SDA), freq=I2C_FREQ)
oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

# LEDs
led1 = Pin(PIN_LED1, Pin.OUT)
led2 = Pin(PIN_LED2, Pin.OUT)
led3 = Pin(PIN_LED3, Pin.OUT)

# Rotary Encoder and Button
encoder_A = Pin(PIN_ENCODER_A, Pin.IN, Pin.PULL_UP)
encoder_B = Pin(PIN_ENCODER_B, Pin.IN, Pin.PULL_UP)
button = Pin(PIN_BUTTON, Pin.IN, Pin.PULL_UP)

# ADC
adc0 = ADC(Pin(PIN_ADC0))
adc1 = ADC(Pin(PIN_ADC1))

# FIFO
fifo = []


# Code
