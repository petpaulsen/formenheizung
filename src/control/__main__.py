import argparse
import asyncio
import configparser
import logging

import zmq
import zmq.asyncio
from control.communication import ZmqServer
from control.system import Raspberry, Relay

from control.controller import PIController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(config_filename, network_port):
    config = configparser.ConfigParser()
    config.read(config_filename)

    if network_port is None:
        network_port = config.getint('controller', 'network_port')
    sample_time = config.getfloat('controller', 'sample_time')
    relay_steps_per_cycle = config.getint('controller', 'relay_steps_per_cycle')
    k_p = config.getfloat('controller', 'k_p')
    k_i = config.getfloat('controller', 'k_i')

    loop = zmq.asyncio.ZMQEventLoop()
    asyncio.set_event_loop(loop)
    with Raspberry() as raspberry:
        relay = Relay(raspberry, relay_steps_per_cycle)
        controller = PIController(raspberry, relay, sample_time, k_p, k_i)
        server = ZmqServer(network_port, controller)
        loop.run_until_complete(server.run())
    loop.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('-p', '--port', type=int)
    args = parser.parse_args()
    main(args.config, args.port)
