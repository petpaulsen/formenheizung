import asyncio
import json

import pandas as pd
import zmq
import zmq.asyncio
from flask import Flask, redirect, url_for, render_template, jsonify, abort

app = Flask(__name__)


def send_request(request):
    loop = zmq.asyncio.ZMQEventLoop()
    asyncio.set_event_loop(loop)
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5556")

    async def send_and_receive():
        await socket.send_json(request)
        return await socket.recv_json()
    send_and_receive_task = asyncio.ensure_future(send_and_receive())
    loop.run_until_complete(asyncio.wait_for(send_and_receive_task, 3))
    socket.close()
    loop.close()
    return send_and_receive_task.result()


trajectory = [(0, 20), (10, 40), (20, 50), (30, 25)]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/cmd/start', methods=['POST'])
def start():
    send_request({'id': 'start', 'trajectory': trajectory})
    return redirect(url_for('index'))


@app.route('/cmd/stop', methods=['POST'])
def stop():
    send_request({'id': 'stop'})
    return redirect(url_for('index'))


@app.route('/measurement')
def get_measurement():
    measurement = send_request({'id': 'measurement'})
    if measurement:
        time, target_temperature, temperature, command_value = zip(*measurement)

        measurement = pd.DataFrame({
            'time': time,
            'temperature': temperature
        })

        reference = pd.DataFrame({
            'time': time,
            'temperature': target_temperature
        })

        data = {
            'measurement': json.loads(measurement.to_json(orient='records')),
            'reference': json.loads(reference.to_json(orient='records'))
        }
    else:
        data = {
            'measurement': [],
            'reference': []
        }
    return jsonify(data)


@app.route('/trajectory')
def get_trajectory():
    #trajectory = jsonify(send_request({'id': 'trajectory'}))
    if trajectory:
        time, target_temperature = zip(*trajectory)

        data = pd.DataFrame({
            'time': time,
            'temperature': target_temperature
        })
        data = json.loads(data.to_json(orient='records'))
    else:
        data = []
    return jsonify(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
