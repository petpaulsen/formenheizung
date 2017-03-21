import asyncio

import numpy as np


class ControllerBase:
    def __init__(self, raspberry, relay, sample_time):
        self._raspberry = raspberry
        self._relay = relay
        self._sample_time = sample_time
        self._stop_controller = False

    async def run(self, trajectory):
        target_trajectory = np.array(trajectory)
        num_samples = int(target_trajectory[-1][0] / self._sample_time) + 1

        try:
            self._stop_controller = False
            current_time = 0.0
            for k in range(num_samples):
                target_temperature = np.interp(
                    current_time,
                    target_trajectory[:, 0],
                    target_trajectory[:, 1],
                    left=0, right=0)
                temperature = self._raspberry.read_temperature()
                command_value = self.calc_command_value(target_temperature, temperature)
                self._relay.step(command_value)

                current_time += self._sample_time
                await asyncio.sleep(self._sample_time)

                if self._stop_controller:
                    break
        finally:
            self._raspberry.set_relay(False)

    def stop(self):
        self._stop_controller = True

    def calc_command_value(self, target_temperature, temperature):
        raise NotImplementedError()
