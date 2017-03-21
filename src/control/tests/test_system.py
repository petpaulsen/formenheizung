import unittest
from unittest.mock import patch, PropertyMock, call

import pyfakefs.fake_filesystem_unittest
import time

from control.system import Raspberry, Relay

GPIO_HIGH = object()
GPIO_LOW = object()
RELAY_PIN_NUMBER = 32


class RaspberryTest(pyfakefs.fake_filesystem_unittest.TestCase):
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

        self.assertListEqual(temperatures, [19.687, 20.187])

    @patch('control.system.GPIO.HIGH', new_callable=PropertyMock, return_value=GPIO_HIGH)
    @patch('control.system.GPIO.output')
    def test_set_relay_high(self, gpio_mock, gpio):
        raspberry = Raspberry()
        raspberry.set_relay(True)
        gpio_mock.assert_called_once_with(RELAY_PIN_NUMBER, GPIO_HIGH)

    @patch('control.system.GPIO.LOW', new_callable=PropertyMock, return_value=GPIO_LOW)
    @patch('control.system.GPIO.output')
    def test_set_relay_low(self, gpio_mock, gpio):
        raspberry = Raspberry()
        raspberry.set_relay(False)
        gpio_mock.assert_called_once_with(RELAY_PIN_NUMBER, GPIO_LOW)

    @patch('control.system.GPIO.cleanup')
    def test_shutdown_gpio_cleanup(self, gpio_mock):
        raspberry = Raspberry()
        raspberry.shutdown()
        gpio_mock.assert_called_once_with()

    @patch('control.system.GPIO.cleanup')
    def test_calling_methods_after_shutdown(self, gpio_mock):
        raspberry = Raspberry()
        raspberry.shutdown()
        with self.assertRaises(ValueError):
            raspberry.read_temperatures()
        with self.assertRaises(ValueError):
            raspberry.set_relay(True)


class RaspberryNo1WireTest(pyfakefs.fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_read_temperature(self):
        raspberry = Raspberry()
        temperatures = raspberry.read_temperatures()

        self.assertListEqual(temperatures, [])


class Raspberry1WireConnectionLossTest(pyfakefs.fake_filesystem_unittest.TestCase):
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
        self.assertListEqual(temperatures, [19.687])

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


class RelaisTest(unittest.TestCase):
    @patch('control.system.Raspberry')
    def test_half_onoff(self, raspberry_mock):
        steps_per_cycle = 5

        relay = Relay(raspberry_mock, steps_per_cycle)

        for k in range(steps_per_cycle):
            relay.step(.5)

        expected_calls = [call(True)] * 3 + [call(False)] * 2
        self.assertListEqual(raspberry_mock.set_relay.mock_calls, expected_calls)

    @patch('control.system.Raspberry')
    def test_all_on(self, raspberry_mock):
        steps_per_cycle = 5

        relay = Relay(raspberry_mock, steps_per_cycle)

        for k in range(steps_per_cycle):
            relay.step(1)

        expected_calls = [call(True)] * 5
        self.assertListEqual(raspberry_mock.set_relay.mock_calls, expected_calls)

    @patch('control.system.Raspberry')
    def test_all_off(self, raspberry_mock):
        steps_per_cycle = 5

        relay = Relay(raspberry_mock, steps_per_cycle)

        for k in range(steps_per_cycle):
            relay.step(0)

        expected_calls = [call(False)] * 5
        self.assertListEqual(raspberry_mock.set_relay.mock_calls, expected_calls)


if __name__ == '__main__':
    unittest.main()
