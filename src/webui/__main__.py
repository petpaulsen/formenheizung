import argparse
import asyncio
import configparser
import io
import json
import logging
from datetime import datetime
from subprocess import run
from zipfile import ZipFile

import pandas as pd
import zmq
import zmq.asyncio
from flask import Flask, Response, redirect, url_for, render_template, jsonify, abort, send_file

controller_port = 5556


app = Flask(__name__)


def send_request(request):
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


trajectory = [(0, 20), (10, 40), (20, 50), (30, 25)]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/settings')
def settings():
    profiles = [
        ('profile1', 'Profil 1'),
        ('profile2', 'Profil 2'),
    ]
    return render_template('settings.html', profiles=profiles)


@app.route('/update')
def update():
    run(['git', 'push'], check=True)

    return render_template('update.html')


@app.route('/cmd/start', methods=['POST'])
def start():
    send_request({'id': 'start', 'trajectory': trajectory})
    return redirect(url_for('index'))


@app.route('/cmd/stop', methods=['POST'])
def stop():
    send_request({'id': 'stop'})
    return redirect(url_for('index'))


@app.route('/status')
def get_status():
    response = send_request({'id': 'status'})
    if response['response'] != 'ok':
        abort(500)
    else:
        status_text = {
            'standby': 'Nicht aktiv',
            'stopping': 'Wird angehalten...',
            'running': 'Aktiv'
        }
        status = status_text.get(response['status'], response['status'])
        return jsonify(status)


@app.route('/measurement')
def get_measurement():
    data = {
        'measurement': [],
        'reference': []
    }
    measurement = send_request({'id': 'measurement'})
    if measurement['response'] != 'ok':
        abort(500)
    elif measurement['measurement']:
        time, target_temperature, temperature, command_value = zip(*measurement['measurement'])

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
    return jsonify(data)


@app.route('/trajectory')
def get_trajectory():
    trajectory = jsonify(send_request({'id': 'trajectory'}))
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


@app.route('/snapshot')
def get_snapshot():
    measurement = send_request({'id': 'measurement'})
    trajectory = send_request({'id': 'trajectory'})
    buffer = io.BytesIO()
    with ZipFile(buffer, 'w') as zipfile:
        zipfile.writestr('measurement.json', json.dumps(measurement))
        zipfile.writestr('trajectory.json', json.dumps(trajectory))
    filename = datetime.now().strftime('data-%Y%m%d-%H%M%S')
    return Response(buffer.getvalue(),
                    mimetype='application/zip',
                    headers={'Content-Disposition': 'attachment;filename={}.zip'.format(filename)})


@app.route('/Profilvorlage.xslx')
def get_profile_template():
    return send_file('Profilvorlage.xslx', as_attachment=True)


@app.errorhandler(500)
def internal_error(exception):
    app.logger.error(exception)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('--http-port', type=int)
    parser.add_argument('--controller-port', type=int)
    parser.add_argument('--log')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)
    if args.controller_port is not None:
        controller_port = args.controller_port
    else:
        controller_port = config.getint('controller', 'network_port')
    if args.http_port is not None:
        http_port = args.http_port
    else:
        http_port = config.getint('webui', 'http_port')

    if args.log is not None:
        file_handler = logging.FileHandler(args.log)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    app.run(host='0.0.0.0', port=http_port)
