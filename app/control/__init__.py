import asyncio
import configparser
import logging

import zmq
import zmq.asyncio

from control.communication import ZmqServer
from control.controller import PIController, FakeController, SystemResponseController
from control.system import Raspberry, Relay


def _to_list(list_str):
    return [float(value) for value in list_str.split(',')]


def main(config_filename, network_port=None, log_filename=None):
    logging.basicConfig(filename=log_filename, filemode='w', level=logging.INFO)
    logger = logging.getLogger('main')

    try:
        config = configparser.ConfigParser()
        config.read(config_filename)

        if network_port is None:
            network_port = config.getint('controller', 'network_port')
        sample_time = config.getfloat('controller', 'sample_time')
        relay_steps_per_cycle = config.getint('controller', 'relay_steps_per_cycle')
        controller_type = config.get('controller', 'controller_type', fallback=None)
        shutdown_temperature = config.getfloat('controller', 'shutdown_temperature')

        logger.info('initializing controller')
        loop = zmq.asyncio.ZMQEventLoop()
        asyncio.set_event_loop(loop)
        with Raspberry() as raspberry:
            relay = Relay(raspberry, relay_steps_per_cycle)
            if controller_type == 'pi':
                k_p = config.getfloat('controller', 'k_p')
                k_i = config.getfloat('controller', 'k_i')
                controller = PIController(raspberry, relay, sample_time, k_p, k_i, shutdown_temperature)
            elif controller_type == 'sysresponse':
                command_trajectory_time = _to_list(config.get('sysresponse_controller', 'command_trajectory_time'))
                command_trajectory_value = _to_list(config.get('sysresponse_controller', 'command_trajectory_value'))
                command_value_trajectory = (command_trajectory_time, command_trajectory_value)
                controller = SystemResponseController(
                    raspberry,
                    relay,
                    sample_time,
                    command_value_trajectory,
                    shutdown_temperature)
            else:
                controller = FakeController(raspberry, relay, sample_time)
            server = ZmqServer(raspberry, controller, network_port)
            loop.run_until_complete(server.run())
        loop.close()
        logger.info('controller shut down')
    except Exception:
        logger.exception('uncaught exception')
        raise
