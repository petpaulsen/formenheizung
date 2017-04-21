import asyncio

import logging
import zmq
import zmq.asyncio


class ZmqServer:
    def __init__(self, controller, port=None):
        self._controller = controller

        context = zmq.asyncio.Context()
        self._socket = context.socket(zmq.REP)
        if port is None:
            self.port = self._socket.bind_to_random_port('tcp://*')
        else:
            self._socket.bind('tcp://*:{}'.format(port))
            self.port = port

    async def run(self):
        shutdown = False
        trajectory = []
        logger = logging.getLogger('communication')
        logger.info('controller initialized, waiting for commands')
        while not shutdown:
            request = await self._socket.recv_json()
            if request['id'] == 'status':
                response = {'response': 'ok', 'status': self._controller.get_state()}
            elif request['id'] == 'start':
                logger.info('starting controller')
                trajectory = request['trajectory']
                asyncio.ensure_future(self._controller.run(trajectory))
                response = {'response': 'ok'}
            elif request['id'] == 'stop':
                logger.info('stopping controller')
                self._controller.stop()
                response = {'response': 'ok'}
            elif request['id'] == 'measurement':
                response = {'response': 'ok', 'measurement': self._controller.get_measurement()}
            elif request['id'] == 'trajectory':
                response = {'response': 'ok', 'trajectory': trajectory}
            elif request['id'] == 'shutdown':
                logger.info('shutting down controller')
                response = {'response': 'ok'}
                shutdown = True
            else:
                logger.warning('received unknown command "{}"'.format(request['id']))
                response = {'response': 'error_unknown_command'}
            await self._socket.send_json(response)
