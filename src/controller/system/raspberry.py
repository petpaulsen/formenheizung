try:
    import RPi.GPIO as GPIO
except ImportError:
    class GPIO:
        HIGH = object()
        LOW = object()

        @staticmethod
        def output(pin, state):
            pass


RELAY_PIN_NUMBER = 32


class Raspberry:
    def __init__(self):
        with open('/sys/devices/w1_bus_master1/w1_master_slaves') as file:
            self._w1_slaves = [line.strip() for line in file.readlines()]

    def read_temperatures(self):
        temperatures = []
        for slave in self._w1_slaves:
            with open('/sys/devices/w1_bus_master1/{}/w1_slave'.format(slave)) as file:
                value = file.readlines()[1].split('t=')[-1]
                temperatures.append(float(value) / 1000)
        return temperatures

    def set_relay(self, value):
        if value:
            GPIO.output(RELAY_PIN_NUMBER, GPIO.HIGH)
        else:
            GPIO.output(RELAY_PIN_NUMBER, GPIO.LOW)
