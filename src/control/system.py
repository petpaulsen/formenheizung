from concurrent.futures import ThreadPoolExecutor
from contextlib import AbstractContextManager
from threading import Event, Lock

try:
    import RPi.GPIO as GPIO
except ImportError:
    class GPIO:
        HIGH = object()
        LOW = object()

        @staticmethod
        def output(pin, state):
            pass

        @staticmethod
        def cleanup():
            pass


RELAY_PIN_NUMBER = 32


class Raspberry(AbstractContextManager):
    def __init__(self):
        self._shutdown = False
        self._cancel_event = Event()
        self._current_temperature_lock = Lock()
        try:
            with open('/sys/devices/w1_bus_master1/w1_master_slaves') as file:
                self._w1_slaves = [line.strip() for line in file.readlines()]
            self._current_temperature = self._read_temperatures()
            self._executor = ThreadPoolExecutor(max_workers=1)
            self._worker = self._executor.submit(self._read_temperature_worker)
        except FileNotFoundError:
            self._w1_slaves = []
            self._current_temperature = []
            self._executor = None
            self._worker = None

    def _read_temperatures(self):
        temperatures = []
        for slave in self._w1_slaves:
            with open('/sys/devices/w1_bus_master1/{}/w1_slave'.format(slave)) as file:
                value = file.readlines()[1].split('t=')[-1]
                temperatures.append(float(value) / 1000)
        return temperatures

    def _read_temperature_worker(self):
        while not self._cancel_event.is_set():
            current_temperature = self._read_temperatures()
            with self._current_temperature_lock:
                self._current_temperature = current_temperature

    def read_temperatures(self):
        if self._shutdown:
            raise ValueError('shutdown was called')
        if self._worker is not None and self._worker.done():
            # check for exceptions raised in the worker thread
            exception = self._worker.exception()
            if exception is not None:
                raise exception
        with self._current_temperature_lock:
            return self._current_temperature

    def set_relay(self, value):
        if self._shutdown:
            raise ValueError('shutdown was called')
        if value:
            GPIO.output(RELAY_PIN_NUMBER, GPIO.HIGH)
        else:
            GPIO.output(RELAY_PIN_NUMBER, GPIO.LOW)

    def shutdown(self):
        if not self._shutdown:
            GPIO.cleanup()

            self._cancel_event.set()
            if self._executor is not None:
                self._executor.shutdown()

            self._shutdown = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


class Relay:
    def __init__(self, raspberry, steps_per_cycle):
        self._raspberry = raspberry
        self._steps_per_cycle = steps_per_cycle
        self._counter = 0

    def step(self, onoff_ratio):
        self._raspberry.set_relay(self._counter < onoff_ratio * self._steps_per_cycle)
        self._counter += 1
        if self._counter >= self._steps_per_cycle:
            self._counter = 0
