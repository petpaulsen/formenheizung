import asyncio
import concurrent.futures
import unittest
from unittest.mock import patch, call

from controller import ControllerBase
from system import Relay


class TestError(Exception):
    pass


class ControllerTest(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    def tearDown(self):
        self.loop.close()

    @patch('system.Relay')
    @patch('system.Raspberry')
    @patch('controller.ControllerBase.calc_command_value')
    def test_simple_trajectory(self, calc_command_value, raspberry_mock, relay_mock):
        calc_command_value.return_value = 0.1
        raspberry_mock.read_temperature.return_value = 20.0

        trajectory = [(0, 20.0), (0.1, 30.0), (0.2, 25.0)]
        controller = ControllerBase(raspberry_mock, relay_mock, sample_time=0.1)

        self.loop.run_until_complete(controller.run(trajectory))

        self.assertListEqual(
            calc_command_value.mock_calls,
            [call(20.0, 20.0), call(30.0, 20.0), call(25.0, 20.0)]
        )
        self.assertListEqual(relay_mock.step.mock_calls, [call(0.1)] * 3)

    @patch('system.Relay')
    @patch('system.Raspberry')
    @patch('controller.ControllerBase.calc_command_value')
    def test_trajectory_interpolation(self, calc_command_value, raspberry_mock, relay_mock):
        calc_command_value.return_value = 0.2
        raspberry_mock.read_temperature.return_value = 20.0

        trajectory = [(0, 20.0), (0.4, 40.0)]
        controller = ControllerBase(raspberry_mock, relay_mock, sample_time=0.1)

        self.loop.run_until_complete(controller.run(trajectory))

        self.assertListEqual(
            calc_command_value.mock_calls,
            [call(20.0, 20.0), call(25.0, 20.0), call(30.0, 20.0), call(35.0, 20.0), call(40.0, 20.0)]
        )
        self.assertListEqual(relay_mock.step.mock_calls, [call(0.2)] * 5)

    @patch('system.Raspberry')
    @patch('controller.ControllerBase.calc_command_value')
    def test_turn_off_relay_when_finished(self, calc_command_value, raspberry_mock):
        calc_command_value.return_value = 1
        raspberry_mock.read_temperature.return_value = 20.0

        trajectory = [(0, 20.0), (0.1, 40.0)]
        relay = Relay(raspberry_mock, steps_per_cycle=10)
        controller = ControllerBase(raspberry_mock, relay, sample_time=0.01)

        self.loop.run_until_complete(controller.run(trajectory))

        self.assertEqual(raspberry_mock.set_relay.mock_calls[-1], call(False))

    @patch('system.Raspberry')
    @patch('controller.ControllerBase.calc_command_value')
    def test_turn_off_relay_when_error(self, calc_command_value, raspberry_mock):
        calc_command_value.side_effect = TestError()
        raspberry_mock.read_temperature.return_value = 20.0

        trajectory = [(0, 20.0), (0.1, 40.0)]
        relay = Relay(raspberry_mock, steps_per_cycle=10)
        controller = ControllerBase(raspberry_mock, relay, sample_time=0.01)

        try:
            self.loop.run_until_complete(controller.run(trajectory))
        except TestError:
            pass

        self.assertEqual(raspberry_mock.set_relay.mock_calls[-1], call(False))

    @patch('system.Relay')
    @patch('system.Raspberry')
    @patch('controller.ControllerBase.calc_command_value')
    def test_stop_controller(self, calc_command_value, relay_mock, raspberry_mock):
        calc_command_value.return_value = 0.0

        trajectory = [(0, 20.0), (1e9, 40.0)]
        controller = ControllerBase(raspberry_mock, relay_mock, sample_time=0.01)

        async def _test():
            controller_future = asyncio.ensure_future(controller.run(trajectory), loop=self.loop)
            await asyncio.sleep(.1)
            controller.stop()
            try:
                await asyncio.wait_for(controller_future, timeout=2)
            except concurrent.futures.TimeoutError:
                self.fail('Controller was not stopped. Test timed out.')

        self.loop.run_until_complete(_test())


if __name__ == '__main__':
    unittest.main()