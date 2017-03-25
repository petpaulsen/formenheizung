import asyncio

import numpy as np


class ControllerBase:
    def __init__(self, raspberry, relay, sample_time):
        self._raspberry = raspberry
        self._relay = relay
        self._stop_controller = False
        self.sample_time = sample_time

    async def run(self, trajectory):
        target_trajectory = np.array(trajectory)
        num_samples = int(target_trajectory[-1][0] / self.sample_time) + 1

        try:
            self._stop_controller = False
            current_time = 0.0
            for k in range(num_samples):
                target_temperature = np.interp(
                    current_time,
                    target_trajectory[:, 0],
                    target_trajectory[:, 1],
                    left=0, right=0)
                temperatures = np.max(self._raspberry.read_temperatures())
                command_value = self.calc_command_value(target_temperature, temperatures)
                self._relay.step(command_value)

                current_time += self.sample_time
                await asyncio.sleep(self.sample_time)

                if self._stop_controller:
                    break
        finally:
            self._raspberry.set_relay(False)

    def stop(self):
        self._stop_controller = True

    def calc_command_value(self, target_temperature, temperature):
        raise NotImplementedError()


class PIController(ControllerBase):
    def __init__(self, raspberry, relay, sample_time, k_p, k_i):
        super(PIController, self).__init__(raspberry, relay, sample_time)
        self.k_p = k_p
        self.k_i = k_i
        self._accumulator = 0.0

    def calc_command_value(self, target_temperature, temperature):
        error = target_temperature - temperature
        self._accumulator += error * self.sample_time
        command_value = self.k_p * error + self.k_i * self._accumulator
        return command_value
