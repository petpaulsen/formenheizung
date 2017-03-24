import asyncio
import zmq
import zmq.asyncio


class ZmqServer:
    def __init__(self, port, controller):
        self._controller = controller

        context = zmq.asyncio.Context()
        self._socket = context.socket(zmq.REP)
        self._socket.bind('tcp://*:{}'.format(port))

    async def run(self):
        shutdown = False
        while not shutdown:
            request = await self._socket.recv_json()
            response = None
            if request['id'] == 'start':
                asyncio.ensure_future(self._controller.run(request['trajectory']))
            elif request['id'] == 'stop':
                self._controller.stop()
            elif request['id'] == 'shutdown':
                shutdown = True
            else:
                response = {'status': 'error'}
            await self._socket.send_json(response)
