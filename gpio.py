from analogio import AnalogIn
from digitalio import DigitalInOut, Direction, Pull
from rotaryio import IncrementalEncoder


class IO:
    def __init__(self, pin):
        self.io = DigitalInOut(pin)

    @property
    def value(self):
        return self.io.value

    @value.setter
    def set_value(self, new_value):
        self.io.value = new_value

    def deinit(self):
        self.io.deinit()
        self.io = None


class Input(IO):
    def __init__(self, pin, default=None):
        super().__init__(pin)
        self.io.direction = Direction.INPUT
        self.io.pull = {True: Pull.UP, False: Pull.DOWN, None: None}[default]


class Output(IO):
    def __init__(self, pin):
        self.io = DigitalInOut(pin)
        self.io.direction = Direction.OUTPUT


class Button(Input):
    def __init__(self, pin, normally_high=True):
        super().__init__(pin, default=normally_high)
        self.inverted = normally_high

    @property
    def pressed(self):
        return (not self.io.value) if self.inverted else self.io.value


class AnalogInput(Input):
    def __init__(self, pin):
        self.io = AnalogIn(pin)

    @property
    def value(self):
        return self.io.value/65536.0


class RotaryInput(Input):
    def __init__(self, left_pin, right_pin):
        self.encoder = IncrementalEncoder(left_pin, right_pin)

    @property
    def value(self):
        return self.encoder.position

    def deinit(self):
        self.encoder.deinit()
