import asyncio

import zmq
import zmq.asyncio
from flask import Flask, redirect, url_for, render_template, make_response, abort

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


@app.route('/start', methods=['POST'])
def start():
    send_request({'id': 'start', 'trajectory': trajectory})
    return redirect(url_for('index'))


@app.route('/stop', methods=['POST'])
def stop():
    send_request({'id': 'stop'})
    return redirect(url_for('index'))


@app.route('/plot')
def plot():
    import io

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure

    measurement = send_request({'id': 'measurement'})
    target_trajectory = send_request({'id': 'trajectory'})
    if not measurement or not target_trajectory:
        abort(404)
    time, temperature, target_temperature, _ = zip(*measurement)
    traj_time, traj_temperature = zip(*target_trajectory)

    fig = Figure()
    ax = fig.add_subplot(111)
    ax.plot(time, temperature, '-')
    #ax.plot(time, target_temperature, 'r:')
    ax.plot(traj_time, traj_temperature, 'r:')
    ax.plot(time[-1], temperature[-1], 'ro')
    ax.set_xlabel('Zeit [s]')
    ax.set_ylabel('Temperatur [°C]')
    ax.grid(True)
    ax.set_ylim(0, 70)

    canvas = FigureCanvas(fig)
    png_output = io.BytesIO()
    canvas.print_png(png_output)

    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0')
