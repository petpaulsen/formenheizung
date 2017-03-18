import atexit

import RPi.GPIO as GPIO

from system import SystemBase


class RaspberrySystem(SystemBase):
    RELAY_PIN_NUMBER = 32

    def __init__(self):
        with open('/sys/devices/w1_bus_master1/w1_master_slaves') as file:
            self._w1_slaves = [line.strip() for line in file.readlines()]
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(RaspberrySystem.RELAY_PIN_NUMBER, GPIO.OUT)
        atexit.register(GPIO.cleanup)

    def set_relay(self, value):
        if value:
            GPIO.output(RaspberrySystem.RELAY_PIN_NUMBER, GPIO.HIGH)
        else:
            GPIO.output(RaspberrySystem.RELAY_PIN_NUMBER, GPIO.LOW)

    def read_temperature(self, index):
        with open('/sys/bus/w1/devices/{}/w1_slave'.format(self._w1_slaves[index])) as file:
            value = file.readlines()[1].split('t=')[-1]
            return float(value) / 1000
