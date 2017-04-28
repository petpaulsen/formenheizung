from multiprocessing import Process

import control
import webui


def run_controller():
    control.main('config.ini')


def run_webui():
    webui.main('config.ini')

if __name__ == '__main__':
    proc_controller = Process(target=run_controller)
    proc_controller.daemon = True
    proc_controller.start()

    proc_webui = Process(target=run_webui)
    proc_webui.daemon = True
    proc_webui.start()

    proc_controller.join()
    proc_webui.join()
