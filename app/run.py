import argparse
from multiprocessing import Process

import control
import webui


def run_controller(log_filename):
    control.main('config.ini', log_filename=log_filename)


def run_webui(log_filename):
    webui.main('config.ini', log_filename=log_filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller-log')
    parser.add_argument('--webui-log')
    args = parser.parse_args()

    proc_controller = Process(target=run_controller, args=(args.controller_log, ))
    proc_controller.daemon = True
    proc_controller.start()

    proc_webui = Process(target=run_webui, args=(args.webui_log, ))
    proc_webui.daemon = True
    proc_webui.start()

    proc_controller.join()
    proc_webui.join()
