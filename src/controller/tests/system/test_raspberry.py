import unittest
from unittest.mock import patch, PropertyMock

import pyfakefs.fake_filesystem_unittest

from system.raspberry import Raspberry


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

    @patch('system.raspberry.GPIO.HIGH', new_callable=PropertyMock, return_value=GPIO_HIGH)
    @patch('system.raspberry.GPIO.output')
    def test_set_relay_high(self, gpio_mock, gpio):
        raspberry = Raspberry()
        raspberry.set_relay(True)
        gpio_mock.assert_called_once_with(RELAY_PIN_NUMBER, GPIO_HIGH)

    @patch('system.raspberry.GPIO.LOW', new_callable=PropertyMock, return_value=GPIO_LOW)
    @patch('system.raspberry.GPIO.output')
    def test_set_relay_low(self, gpio_mock, gpio):
        raspberry = Raspberry()
        raspberry.set_relay(False)
        gpio_mock.assert_called_once_with(RELAY_PIN_NUMBER, GPIO_LOW)


if __name__ == '__main__':
    unittest.main()
