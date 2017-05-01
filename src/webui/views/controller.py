import asyncio
import io
import json
from datetime import datetime
from zipfile import ZipFile

import pandas as pd
import zmq
import zmq.asyncio
from flask import Blueprint, Response, jsonify, abort, current_app, request

from webui.profiles import load_profiles

controller = Blueprint(
    'controller', __name__,
    url_prefix='/controller',
    template_folder='templates',
    static_folder='static')


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


@controller.route('/start', methods=['POST'])
def start():
    profile_id = request.form['temperatureprofile']
    profile = load_profiles()[profile_id]

    send_request({'id': 'start', 'trajectory': profile.trajectory})
    return Response()


@controller.route('/stop', methods=['POST'])
def stop():
    send_request({'id': 'stop'})
    return Response()


@controller.route('/status')
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


@controller.route('/measurement')
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
        time = [t / 60.0 for t in time]  # convert to minutes

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


@controller.route('/trajectory')
def get_trajectory():
    trajectory = send_request({'id': 'trajectory'})
    if trajectory['response'] == 'ok' and trajectory['trajectory']:
        time, target_temperature = zip(*trajectory['trajectory'])
        time = [t / 60.0 for t in time]  # convert to minutes

        data = pd.DataFrame({
            'time': time,
            'temperature': target_temperature
        })
        data = json.loads(data.to_json(orient='records'))
    else:
        data = []
    return jsonify(data)


@controller.route('/snapshot')
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
