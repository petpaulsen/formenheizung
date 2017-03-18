import asyncio
import configparser
import logging

import zmq
import zmq.asyncio

from controller import Controller

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainLoop:
    def __init__(self, config):
        context = zmq.asyncio.Context()
        self._socket = context.socket(zmq.REP)
        self._socket.bind('tcp://*:{}'.format(config.getint('controller', 'network_port')))
        self._message_queue = asyncio.Queue()
        self._controller = Controller(
            config.getfloat('controller', 'sample_time'),
            config.getint('controller', 'relais_steps_per_cycle')
        )

    async def run(self):
        controller_task = asyncio.ensure_future(self._controller.run())

        logger.info('controller ready')
        while not controller_task.done():
            request = await self._socket.recv_json()
            if request['id'] == 'shutdown':
                logger.info('shutting down')
                controller_task.cancel()
                await asyncio.sleep(0)
                await self._socket.send_json(None)
            elif request['id'] == 'start':
                logger.info('starting controller')
                await self._controller.set_trajectory(request['trajectory'])
                await self._socket.send_json(None)
            elif request['id'] == 'stop':
                logger.info('stopping controller')
                await self._controller.set_trajectory(None)
                await self._socket.send_json(None)
            elif request['id'] == 'measurement':
                #logger.info('getting measurement')
                await self._socket.send_json(self._controller.get_measurement())
            elif request['id'] == 'trajectory':
                #logger.info('getting trajectory')
                await self._socket.send_json(self._controller.get_trajectory())
            else:
                await self._socket.send_json(ValueError())
        if not controller_task.cancelled():
            await controller_task


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    loop = zmq.asyncio.ZMQEventLoop()
    asyncio.set_event_loop(loop)

    main_loop = MainLoop(config)

    loop.run_until_complete(main_loop.run())
    loop.close()

if __name__ == '__main__':
    main()
