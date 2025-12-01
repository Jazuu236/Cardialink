class cMenuState:
    class cInputHandlerState:
        def __init__(self):
            self.current_position = 0
            self.button_has_been_released = True
    def __init__(self):
        self.current_page = 0
        self.hrv_measurement_started_ts = 0
        self.input_handler = self.cInputHandlerState()
