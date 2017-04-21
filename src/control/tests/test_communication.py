import asyncio
import functools
import unittest
from contextlib import closing
from unittest.mock import patch

import zmq
import zmq.asyncio

from control.communication import ZmqServer


def commmunication_test(shutdown=False, timeout=3):
    def wrap(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with closing(zmq.asyncio.ZMQEventLoop()) as loop, patch('control.controller.ControllerBase') as controller:
                asyncio.set_event_loop(loop)
                server = ZmqServer(controller)

                client_context = zmq.asyncio.Context()
                with client_context.socket(zmq.REQ) as client_socket:
                    async def client(*client_args, **client_kwargs):
                        result = await func(*client_args, **client_kwargs)
                        if shutdown:
                            await client_socket.send_json({'id': 'shutdown'})
                            await client_socket.recv_json()
                        return result

                    client_socket.connect('tcp://localhost:{}'.format(server.port))
                    tasks = asyncio.gather(server.run(), client(*args, client_socket, controller, **kwargs))
                    try:
                        loop.run_until_complete(asyncio.wait_for(tasks, timeout=timeout, loop=loop))
                    finally:
                        tasks = asyncio.Task.all_tasks(loop)
                        if tasks:
                            for task in tasks:
                                task.cancel()
                            loop.run_until_complete(asyncio.wait(tasks))
        return wrapper
    return wrap


class ZmqServerTest(unittest.TestCase):
    @commmunication_test()
    async def test_shutdown(self, socket, controller):
        await socket.send_json({'id': 'shutdown'})
        return_value = await socket.recv_json()
        self.assertEqual(return_value, {'response': 'ok'})

    @commmunication_test(shutdown=True)
    async def test_unknown_message_id_returns_error(self, socket, controller):
        await socket.send_json({'id': 'invalid_command_id'})
        return_value = await socket.recv_json()
        self.assertEqual(return_value, {'response': 'error_unknown_command'})

    @commmunication_test(shutdown=True)
    async def test_start_controller(self, socket, controller):
        async def coroutine():
            pass
        controller.run.return_value = coroutine()
        trajectory = [[0, 10], [1, 18], [2, 25]]
        await socket.send_json({'id': 'start', 'trajectory': trajectory})
        result = await socket.recv_json()
        controller.run.assert_called_once_with(trajectory)
        self.assertEqual(result, {'response': 'ok'})

    @commmunication_test(shutdown=True)
    async def test_stop_controller(self, socket, controller):
        await socket.send_json({'id': 'stop'})
        result = await socket.recv_json()
        controller.stop.assert_called_once_with()
        self.assertEqual(result, {'response': 'ok'})

    @commmunication_test(shutdown=True)
    async def test_get_trajectory_before_controller_is_started(self, socket, controller):
        await socket.send_json({'id': 'trajectory'})
        result = await socket.recv_json()
        self.assertEqual(result, {'response': 'ok', 'trajectory': []})

    @commmunication_test(shutdown=True)
    async def test_get_trajectory_after_controller_is_started(self, socket, controller):
        async def coroutine():
            pass
        controller.run.return_value = coroutine()
        trajectory = [[0, 10], [1, 18], [2, 25]]
        await socket.send_json({'id': 'start', 'trajectory': trajectory})
        await socket.recv_json()
        await socket.send_json({'id': 'trajectory'})
        result = await socket.recv_json()
        self.assertEqual(result, {'response': 'ok', 'trajectory': trajectory})

    @commmunication_test(shutdown=True)
    async def test_get_trajectory_before_controller_is_started(self, socket, controller):
        measurement = [
            [0, 10, 20, 0.1],
            [1, 15, 30, 0.5],
            [2, 20, 50, 0.2],
        ]
        controller.get_measurement.return_value = measurement
        await socket.send_json({'id': 'measurement'})
        result = await socket.recv_json()
        self.assertEqual(result, {'response': 'ok', 'measurement': measurement})

    @commmunication_test(shutdown=True)
    async def test_status(self, socket, controller):
        controller.get_state.return_value = 'some_status'
        await socket.send_json({'id': 'status'})
        result = await socket.recv_json()
        self.assertEqual(result, {'response': 'ok', 'status': 'some_status'})


if __name__ == '__main__':
    unittest.main()
