import asyncio
import concurrent.futures
import unittest
from unittest.mock import patch

import zmq
import zmq.asyncio

from control.communication import ZmqServer
from control.tests.helpers import async_test

PORT = 5556


class ZmqServerTest(unittest.TestCase):

    def setUp(self):
        self.loop = zmq.asyncio.ZMQEventLoop()
        asyncio.set_event_loop(self.loop)
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect('tcp://localhost:{}'.format(PORT))

    def tearDown(self):
        self.socket.close()
        self.loop.close()

    @patch('control.controller.ControllerBase')
    def test_communication(self, controller_mock):
        controller_trajectories = []
        async def run_controller(trajectory):
            controller_trajectories.append(trajectory)
        controller_mock.run = run_controller

        trajectory = [[0, 10], [1, 18], [2, 25]]
        server = ZmqServer(PORT, controller_mock)

        async def _send_receive():
            await self.socket.send_json({'id': 'start', 'trajectory': trajectory})
            await self.socket.recv_json()
            await self.socket.send_json({'id': 'stop'})
            await self.socket.recv_json()
            await self.socket.send_json({'id': 'shutdown'})

        async def _test():
            try:
                await asyncio.wait_for(send_receive_future, timeout=2)
            except concurrent.futures.TimeoutError:
                self.fail('Server did not respond. Test timed out.')
            try:
                await asyncio.wait_for(server_future, timeout=2)
            except concurrent.futures.TimeoutError:
                self.fail('Server was not shut down. Test timed out.')

        server_future = asyncio.ensure_future(server.run(), loop=self.loop)
        send_receive_future = asyncio.ensure_future(_send_receive(), loop=self.loop)
        self.loop.run_until_complete(_test())

        self.assertListEqual(controller_trajectories, [trajectory])
        controller_mock.stop.assert_called_once_with()

    @patch('control.controller.ControllerBase')
    def test_unknown_message_id(self, controller_mock):
        server = ZmqServer(PORT, controller_mock)

        async def _send_receive():
            await self.socket.send_json({'id': 'invalid_command_id'})
            return_value = await self.socket.recv_json()
            await self.socket.send_json({'id': 'shutdown'})
            await self.socket.recv_json()
            self.assertDictEqual(return_value, {'status': 'error'})

        async def _test():
            try:
                await asyncio.wait_for(send_receive_future, timeout=2)
            except concurrent.futures.TimeoutError:
                self.fail('Server did not respond. Test timed out.')
            try:
                await asyncio.wait_for(server_future, timeout=2)
            except concurrent.futures.TimeoutError:
                self.fail('Server was not shut down. Test timed out.')

        server_future = asyncio.ensure_future(server.run(), loop=self.loop)
        send_receive_future = asyncio.ensure_future(_send_receive(), loop=self.loop)
        self.loop.run_until_complete(_test())


if __name__ == '__main__':
    unittest.main()
