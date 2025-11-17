import time

class cGUI:
    def __init__(self, oled):
        self.oled = oled

    def draw_page_init(self):
        self.oled.fill(0)
        self.oled.text("Initializing", 0, 0)
        self.oled.show()

    def draw_main_menu(self, current_selection):
        self.oled.fill(0)
        self.oled.text("Encoder:", 0, 0)
        if fifo:
            self.oled.text(fifo[-1], 0, 10)
        self.oled.show()