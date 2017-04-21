import unittest
from unittest.mock import patch, PropertyMock, call

import pyfakefs.fake_filesystem_unittest
import time

from control.system import Raspberry, Relay, GPIO, RELAY_PIN_NUMBER


@patch('control.system.GPIO.output')
class RaspberryRelayTest(unittest.TestCase):
    def test_set_relay_high(self, gpio_mock):
        raspberry = Raspberry()
        raspberry.set_relay(True)
        gpio_mock.assert_called_once_with(RELAY_PIN_NUMBER, GPIO.HIGH)

    def test_set_relay_low(self, gpio_mock):
        raspberry = Raspberry()
        raspberry.set_relay(False)
        gpio_mock.assert_called_once_with(RELAY_PIN_NUMBER, GPIO.LOW)


class RaspberryShutdownTest(unittest.TestCase):
    @patch('control.system.GPIO.cleanup')
    def test_gpio_cleanup_is_called_once(self, gpio_mock):
        raspberry = Raspberry()
        raspberry.shutdown()
        raspberry.shutdown()
        gpio_mock.assert_called_once_with()

    @patch('control.system.GPIO.cleanup')
    def test_context_manager_calls_cleanup(self, gpio_mock):
        with Raspberry():
            pass
        gpio_mock.assert_called_once_with()

    def test_set_relay_raises_exception_after_shutdown(self):
        raspberry = Raspberry()
        raspberry.shutdown()
        with self.assertRaises(ValueError):
            raspberry.set_relay(True)

    def test_read_temperature_raises_exception_after_shutdown(self):
        raspberry = Raspberry()
        raspberry.shutdown()
        with self.assertRaises(ValueError):
            raspberry.read_temperatures()


class RaspberryTemperatureTest(pyfakefs.fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.fs.CreateFile(
            '/sys/devices/w1_bus_master1/w1_master_slaves',
            contents='28-0000085b4837\n'
                     '28-0000085b4838\n'
        )
        self.fs.CreateFile(
            '/sys/devices/w1_bus_master1/28-0000085b4837/w1_slave',
            contents='3b 01 4b 46 7f ff 05 10 54 : crc=54 YES\n'
                     '3b 01 4b 46 7f ff 05 10 54 t=19687'
        )
        self.fs.CreateFile(
            '/sys/devices/w1_bus_master1/28-0000085b4838/w1_slave',
            contents='43 01 4b 46 7f ff 0d 10 bd : crc=bd YES\n'
                     '43 01 4b 46 7f ff 0d 10 bd t=20187'
        )

    def test_read_temperature(self):
        raspberry = Raspberry()
        temperatures = raspberry.read_temperatures()

        self.assertEqual(temperatures, [19.687, 20.187])


class RaspberryTemperatureNo1WireTest(pyfakefs.fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_read_temperature(self):
        raspberry = Raspberry()
        temperatures = raspberry.read_temperatures()

        self.assertEqual(temperatures, [])


class RaspberryTemperature1WireConnectionLossTest(pyfakefs.fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.fs.CreateFile(
            '/sys/devices/w1_bus_master1/w1_master_slaves',
            contents='28-0000085b4837\n'
        )
        self.fs.CreateFile(
            '/sys/devices/w1_bus_master1/28-0000085b4837/w1_slave',
            contents='3b 01 4b 46 7f ff 05 10 54 : crc=54 YES\n'
                     '3b 01 4b 46 7f ff 05 10 54 t=19687'
        )

    def test_connection_loss(self):
        raspberry = Raspberry()
        temperatures = raspberry.read_temperatures()
        self.assertEqual(temperatures, [19.687])

        while True:
            # The file is accessed asynchronously, so deleting the file may fail, because it is still open.
            # In this case repeat until the file is closed.
            try:
                self.fs.RemoveObject('/sys/devices/w1_bus_master1/28-0000085b4837/w1_slave')
                break
            except PermissionError:
                pass
        time.sleep(1)

        with self.assertRaises(FileNotFoundError):
            raspberry.read_temperatures()


class RelayTest(unittest.TestCase):
    @patch('control.system.Raspberry')
    def assert_relay_cycle(self, onoff_ratio, expected, steps_per_cycle, raspberry_mock):
        relay = Relay(raspberry_mock, steps_per_cycle)

        for k in range(steps_per_cycle):
            relay.step(onoff_ratio)

        expected_calls = [call(value) for value in expected]
        self.assertEqual(raspberry_mock.set_relay.mock_calls, expected_calls)

    def test_half_onoff(self):
        self.assert_relay_cycle(.5, [True] * 3 + [False] * 2, 5)

    def test_all_on(self):
        self.assert_relay_cycle(1, [True] * 5, 5)

    def test_all_off(self):
        self.assert_relay_cycle(0, [False] * 5, 5)

    def test_invalid_onoff_ratio(self):
        self.assert_relay_cycle(2, [True] * 5, 5)

    def test_invalid_onoff_ratio_negative(self):
        self.assert_relay_cycle(-1, [False] * 5, 5)


if __name__ == '__main__':
    unittest.main()
