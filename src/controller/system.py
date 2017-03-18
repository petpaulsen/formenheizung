def init():
    raise NotImplementedError()


def set_relay(value):
    raise NotImplementedError()


def read_temperature(index):
    raise NotImplementedError()


class Relais:
    def __init__(self, steps_per_cycle):
        self._counter = 0
        self._steps_per_cycle = steps_per_cycle

    def step(self, onoff_ratio):
        set_relay(self._counter >= onoff_ratio * self._steps_per_cycle)
        self._counter += 1
        if self._counter >= self._steps_per_cycle:
            self._counter = 0
