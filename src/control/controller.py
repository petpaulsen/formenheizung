import asyncio

import numpy as np


class ControllerBase:
    def __init__(self, raspberry, relay, sample_time):
        self._raspberry = raspberry
        self._relay = relay
        self._stop_controller = False
        self._measurement = []
        self.sample_time = sample_time
        self._state = 'standby'

    def get_state(self):
        return self._state

    async def run(self, trajectory):
        target_trajectory = np.array(trajectory)
        num_samples = int(target_trajectory[-1][0] / self.sample_time) + 1

        try:
            self._measurement = []
            self._stop_controller = False
            current_time = 0.0
            self._state = 'running'
            for k in range(num_samples):
                target_temperature = np.interp(
                    current_time,
                    target_trajectory[:, 0],
                    target_trajectory[:, 1],
                    left=0, right=0)
                temperature = np.max(self._raspberry.read_temperatures())
                command_value = self.calc_command_value(current_time, target_temperature, temperature)
                self._relay.step(command_value)

                self._measurement.append((current_time, target_temperature, temperature, command_value))

                current_time += self.sample_time
                await asyncio.sleep(self.sample_time)

                if self._stop_controller:
                    break
        finally:
            self._raspberry.set_relay(False)
            self._state = 'standby'

    def stop(self):
        self._state = 'stopping'
        self._stop_controller = True

    def get_measurement(self):
        return self._measurement

    def calc_command_value(self, time, target_temperature, temperature):
        raise NotImplementedError()


class PIController(ControllerBase):
    def __init__(self, raspberry, relay, sample_time, k_p, k_i):
        super(PIController, self).__init__(raspberry, relay, sample_time)
        self.k_p = k_p
        self.k_i = k_i
        self._accumulator = 0.0

    def calc_command_value(self, time, target_temperature, temperature):
        error = target_temperature - temperature
        self._accumulator += error * self.sample_time
        command_value = self.k_p * error + self.k_i * self._accumulator
        return command_value


class SystemResponseController(ControllerBase):
    def __init__(self, raspberry, relay, sample_time, command_value_trajectory):
        super(SystemResponseController, self).__init__(raspberry, relay, sample_time)
        self.command_value_trajectory = command_value_trajectory

    def calc_command_value(self, time, target_temperature, temperature):
        return np.interp(time, self.command_value_trajectory[0], self.command_value_trajectory[1])


class FakeController(ControllerBase):
    class FakeRaspberry:
        def __init__(self):
            self._temperature = 40

        def read_temperatures(self):
            grad = float(np.random.rand(1)) - .5
            self._temperature += grad
            return [self._temperature]

        def set_relay(self, value):
            pass

    class FakeRelay:
        def step(self, onoff_ratio):
            pass

    def __init__(self, raspberry, relay, sample_time):
        fake_raspberry = FakeController.FakeRaspberry()
        fake_relay = FakeController.FakeRelay()
        super(FakeController, self).__init__(fake_raspberry, fake_relay, sample_time)

    def calc_command_value(self, time, target_temperature, temperature):
        return float(np.random.rand(1))
