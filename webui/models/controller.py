import asyncio

import zmq
import zmq.asyncio
from flask import current_app


def send_request(request):
    controller_port = current_app.config['CONTROLLER_PORT']

    loop = zmq.asyncio.ZMQEventLoop()
    asyncio.set_event_loop(loop)
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REQ)
    socket.connect('tcp://localhost:{}'.format(controller_port))

    async def send_and_receive():
        await socket.send_json(request)
        return await socket.recv_json()

    send_and_receive_task = asyncio.ensure_future(send_and_receive())
    loop.run_until_complete(asyncio.wait_for(send_and_receive_task, timeout=3))
    socket.close()
    loop.close()
    return send_and_receive_task.result()
