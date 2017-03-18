import asyncio

import numpy as np

from system import Relay, read_temperature, set_relay


class Controller:
    def __init__(self, sample_time=0.1, relay_steps_per_cycle=10):
        self._relay = Relay(relay_steps_per_cycle)
        self._sample_time = sample_time
        self._trajectory = asyncio.Queue(maxsize=1)
        self._measurement = []
        self._target_trajectory = []

    async def run(self):
        while True:
            while True:
                target_trajectory = await self._trajectory.get()
                if target_trajectory is not None:
                    break
            self._target_trajectory = target_trajectory
            trajectory = np.array(target_trajectory)
            num_samples = int(trajectory[-1][0] / self._sample_time)
            current_time = 0.0
            self._measurement = []

            try:
                for t in range(num_samples):
                    if not self._trajectory.empty():
                        # a new trajectory is available, so cancel this one and process the new
                        break

                    target_temperature = np.interp(
                        current_time,
                        trajectory[:, 0],
                        trajectory[:, 1],
                        left=0, right=0)
                    temperature = (read_temperature(0) + read_temperature(1)) / 2

                    onoff_ratio = self._calc_command_value(target_temperature, temperature)
                    self._relay.step(onoff_ratio)

                    self._measurement.append((current_time, temperature, target_temperature, onoff_ratio))

                    current_time += self._sample_time
                    await asyncio.sleep(self._sample_time)
            finally:
                # when the controller finishes turn the relay off
                set_relay(False)

    async def set_trajectory(self, trajectory):
        await self._trajectory.put(trajectory)

    def get_measurement(self):
        return self._measurement

    def get_trajectory(self):
        return self._target_trajectory

    def _calc_command_value(self, target_temperature, temperature):
        return 0.0 #raise NotImplementedError()
