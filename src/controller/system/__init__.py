class SystemBase:
    def set_relay(self, value):
        raise NotImplementedError()

    def read_temperature(self, index):
        raise NotImplementedError()


class FakeSystem(SystemBase):
    def set_relay(self, value):
        pass

    def read_temperature(self, index):
        import numpy as np
        return 15 + 5 * np.random.rand(1)[0]

try:
    from system.raspberry import RaspberrySystem
    system = RaspberrySystem()
except ImportError:
    system = FakeSystem()

set_relay = system.set_relay
read_temperature = system.read_temperature


class Relay:
    def __init__(self, steps_per_cycle):
        self._counter = 0
        self._steps_per_cycle = steps_per_cycle

    def step(self, onoff_ratio):
        set_relay(self._counter >= onoff_ratio * self._steps_per_cycle)
        self._counter += 1
        if self._counter >= self._steps_per_cycle:
            self._counter = 0
