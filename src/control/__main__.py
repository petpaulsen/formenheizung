import argparse
import asyncio
import configparser
import logging

import zmq
import zmq.asyncio
from control.communication import ZmqServer
from control.system import Raspberry, Relay

from control.controller import PIController, FakeController, SystemResponseController


def _to_list(list_str):
    return [float(value) for value in list_str.split(',')]


def main(config_filename, network_port, log_filename, controller):
    logging.basicConfig(filename=log_filename, filemode='w', level=logging.INFO)
    logger = logging.getLogger('main')

    try:
        config = configparser.ConfigParser()
        config.read(config_filename)

        if network_port is None:
            network_port = config.getint('controller', 'network_port')
        sample_time = config.getfloat('controller', 'sample_time')
        relay_steps_per_cycle = config.getint('controller', 'relay_steps_per_cycle')

        logger.info('initializing controller')
        loop = zmq.asyncio.ZMQEventLoop()
        asyncio.set_event_loop(loop)
        with Raspberry() as raspberry:
            relay = Relay(raspberry, relay_steps_per_cycle)
            if controller == 'pi':
                k_p = config.getfloat('controller', 'k_p')
                k_i = config.getfloat('controller', 'k_i')
                controller = PIController(raspberry, relay, sample_time, k_p, k_i)
            elif controller == 'sysresponse':
                command_trajectory_time = _to_list(config.get('sysresponse_controller', 'command_trajectory_time'))
                command_trajectory_value = _to_list(config.get('sysresponse_controller', 'command_trajectory_value'))
                command_value_trajectory = (command_trajectory_time, command_trajectory_value)
                controller = SystemResponseController(raspberry, relay, sample_time, command_value_trajectory)
            else:
                controller = FakeController(raspberry, relay, sample_time)
            server = ZmqServer(controller, network_port)
            loop.run_until_complete(server.run())
        loop.close()
        logger.info('controller shut down')
    except Exception:
        logger.exception('uncaught exception')
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('-p', '--port', type=int)
    parser.add_argument('--log')
    parser.add_argument('--controller')
    args = parser.parse_args()
    main(args.config, args.port, args.log, args.controller)
