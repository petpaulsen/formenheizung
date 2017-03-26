import asyncio

import logging
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
        trajectory = []
        logger = logging.getLogger('communication')
        logger.info('controller initialized, waiting for commands')
        while not shutdown:
            request = await self._socket.recv_json()
            response = None
            if request['id'] == 'start':
                logger.info('starting controller')
                trajectory = request['trajectory']
                asyncio.ensure_future(self._controller.run(trajectory))
            elif request['id'] == 'stop':
                logger.info('stopping controller')
                self._controller.stop()
            elif request['id'] == 'measurement':
                response = self._controller.get_measurement()
            elif request['id'] == 'trajectory':
                response = trajectory
            elif request['id'] == 'shutdown':
                logger.info('shutting down controller')
                shutdown = True
            else:
                logger.warning('received unknown command "{}"'.format(request['id']))
                response = {'status': 'error'}
            await self._socket.send_json(response)
