import asyncio
import concurrent.futures
import unittest
from unittest.mock import patch, call

from control.controller import ControllerBase
from control.system import Relay
from tests.helper import async_test


class CommunicationTimeoutError(Exception):
    pass


@patch('control.system.Relay')
@patch('control.system.Raspberry')
@patch('control.controller.ControllerBase.calc_command_value')
class ControllerTest(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    def tearDown(self):
        self.loop.close()

    def test_simple_trajectory(self, calc_command_value, raspberry_mock, relay_mock):
        calc_command_value.return_value = 0.1
        raspberry_mock.read_temperatures.return_value = [20.0]

        trajectory = [(0, 20.0), (0.1, 30.0), (0.2, 25.0)]
        controller = ControllerBase(raspberry_mock, relay_mock, sample_time=0.1, shutdown_temperature=60)

        self.loop.run_until_complete(controller.run(trajectory))

        self.assertListEqual(
            calc_command_value.mock_calls,
            [call(0.0, 20.0, 20.0), call(0.1, 30.0, 20.0), call(0.2, 25.0, 20.0)]
        )
        self.assertListEqual(relay_mock.step.mock_calls, [call(0.1)] * 3)

    def test_trajectory_interpolation(self, calc_command_value, raspberry_mock, relay_mock):
        calc_command_value.return_value = 0.2
        raspberry_mock.read_temperatures.return_value = [20.0]

        trajectory = [(0, 20.0), (2, 40.0)]
        controller = ControllerBase(raspberry_mock, relay_mock, sample_time=1, shutdown_temperature=60)

        self.loop.run_until_complete(controller.run(trajectory))

        self.assertListEqual(
            calc_command_value.mock_calls,
            [
                call(0, 20.0, 20.0),
                call(1, 30.0, 20.0),
                call(2, 40.0, 20.0),
            ]
        )
        self.assertListEqual(relay_mock.step.mock_calls, [call(0.2)] * 3)

    def test_turn_off_relay_when_finished(self, calc_command_value, raspberry_mock, relay_mock):
        calc_command_value.return_value = 1
        raspberry_mock.read_temperatures.return_value = [20.0]

        trajectory = [(0, 20.0), (0.1, 40.0)]
        relay = Relay(raspberry_mock, steps_per_cycle=10)
        controller = ControllerBase(raspberry_mock, relay, sample_time=0.01, shutdown_temperature=60)

        self.loop.run_until_complete(controller.run(trajectory))

        self.assertEqual(raspberry_mock.set_relay.mock_calls[-1], call(False))

    def test_turn_off_relay_when_error(self, calc_command_value, raspberry_mock, relay_mock):
        calc_command_value.side_effect = CommunicationTimeoutError()
        raspberry_mock.read_temperatures.return_value = [20.0]

        trajectory = [(0, 20.0), (0.1, 40.0)]
        relay = Relay(raspberry_mock, steps_per_cycle=10)
        controller = ControllerBase(raspberry_mock, relay, sample_time=0.01, shutdown_temperature=60)

        try:
            self.loop.run_until_complete(controller.run(trajectory))
        except CommunicationTimeoutError:
            pass

        self.assertEqual(raspberry_mock.set_relay.mock_calls[-1], call(False))

    def test_stop_controller(self, calc_command_value, raspberry_mock, relay_mock):
        calc_command_value.return_value = 0.0
        raspberry_mock.read_temperatures.return_value = [20.0]

        trajectory = [(0, 20.0), (1e9, 40.0)]
        controller = ControllerBase(raspberry_mock, relay_mock, sample_time=0.01, shutdown_temperature=60)

        async def _test():
            controller_future = asyncio.ensure_future(controller.run(trajectory), loop=self.loop)
            await asyncio.sleep(.1)
            controller.stop()
            try:
                await asyncio.wait_for(controller_future, timeout=2)
            except concurrent.futures.TimeoutError:
                self.fail('Controller was not stopped. Test timed out.')

        self.loop.run_until_complete(_test())

    def test_temperature_calculation(self, calc_command_value, raspberry_mock, relay_mock):
        calc_command_value.return_value = 0.1
        raspberry_mock.read_temperatures.return_value = [20.0, 30.0]

        trajectory = [(0, 20.0), (0.1, 30.0), (0.2, 25.0)]
        controller = ControllerBase(raspberry_mock, relay_mock, sample_time=0.1, shutdown_temperature=60)

        self.loop.run_until_complete(controller.run(trajectory))

        self.assertListEqual(
            calc_command_value.mock_calls,
            [call(0.0, 20.0, 30.0), call(0.1, 30.0, 30.0), call(0.2, 25.0, 30.0)]
        )
        self.assertListEqual(relay_mock.step.mock_calls, [call(0.1)] * 3)

    def test_temperature_shutdown(self, calc_command_value, raspberry_mock, relay_mock):
        calc_command_value.return_value = 0.1
        raspberry_mock.read_temperatures.side_effect = [50.0, 70.0, 50.0]

        trajectory = [(0, 20.0), (0.1, 30.0), (0.2, 25.0)]
        controller = ControllerBase(raspberry_mock, relay_mock, sample_time=0.1, shutdown_temperature=60)

        self.loop.run_until_complete(controller.run(trajectory))

        self.assertListEqual(calc_command_value.mock_calls, [call(0.0, 20.0, 50.0)])
        self.assertListEqual(relay_mock.step.mock_calls, [call(0.1)])

    def test_measurement(self, calc_command_value, raspberry_mock, relay_mock):
        calc_command_value.return_value = 0.1
        raspberry_mock.read_temperatures.return_value = [20.0]

        trajectory = [(0, 20.0), (0.1, 30.0), (0.2, 25.0)]
        controller = ControllerBase(raspberry_mock, relay_mock, sample_time=0.1, shutdown_temperature=60)

        self.loop.run_until_complete(controller.run(trajectory))

        self.assertListEqual(
            controller.get_measurement(),
            [(0, 20.0, 20.0, 0.1), (0.1, 30.0, 20.0, 0.1), (0.2, 25.0, 20.0, 0.1)]
        )

    @async_test
    async def test_controller_status(self, calc_command_value, raspberry_mock, relay_mock):
        calc_command_value.return_value = 0.1
        trajectory = [(0, 20.0), (0.1, 30.0), (0.2, 25.0)]
        raspberry_mock.read_temperatures.return_value = [20.0]

        controller = ControllerBase(raspberry_mock, relay_mock, sample_time=0.1, shutdown_temperature=60)
        self.assertEqual(controller.get_state(), 'standby')

        controller_future = asyncio.ensure_future(controller.run(trajectory))
        await asyncio.sleep(0)
        self.assertEqual(controller.get_state(), 'running')

        await controller_future
        self.assertEqual(controller.get_state(), 'standby')

    @async_test
    async def test_controller_status_when_stopped(self, calc_command_value, raspberry_mock, relay_mock):
        calc_command_value.return_value = 0.1
        trajectory = [(0, 20.0), (10, 30.0), (20, 25.0)]
        raspberry_mock.read_temperatures.return_value = [20.0]

        controller = ControllerBase(raspberry_mock, relay_mock, sample_time=0.1, shutdown_temperature=60)
        self.assertEqual(controller.get_state(), 'standby')

        controller_future = asyncio.ensure_future(controller.run(trajectory))
        await asyncio.sleep(0)
        self.assertEqual(controller.get_state(), 'running')

        controller.stop()
        self.assertEqual(controller.get_state(), 'stopping')
        await controller_future
        self.assertEqual(controller.get_state(), 'standby')

if __name__ == '__main__':
    unittest.main()
