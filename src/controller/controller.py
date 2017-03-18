import asyncio

import numpy as np

from system import Relais, read_temperature, set_relay


class Controller:
    def __init__(self, sample_time=0.1, relais_steps_per_cycle=10):
        self._relais = Relais(relais_steps_per_cycle)
        self._sample_time = sample_time
        self._trajectory = asyncio.Queue(maxsize=1)

    async def run(self):
        while True:
            while True:
                trajectory = await self._trajectory.get()
                if trajectory is not None:
                    break
            trajectory = np.array(trajectory)
            num_samples = int(trajectory[-1][0] / self._sample_time)
            current_time = 0.0

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
                    self._relais.step(onoff_ratio)

                    current_time += self._sample_time
                    await asyncio.sleep(self._sample_time)
            finally:
                # when the controller finishes turn the relais off
                set_relay(False)

    async def set_trajectory(self, trajectory):
        await self._trajectory.put(trajectory)

    def _calc_command_value(self, target_temperature, temperature):
        raise NotImplementedError()