import json
import os.path

import pandas as pd
from flask import Blueprint, render_template, jsonify, request

from webui.models.profiles import load_profiles, load_profile

plot = Blueprint(
    'plot', __name__,
    url_prefix='/plot',
    template_folder='templates',
    static_folder='static')


@plot.route('/')
def index():
    profiles = [(profileid, name) for profileid, (name, _) in load_profiles().items()]
    return render_template('plot.html', profiles=profiles)


@plot.route('/trajectory-preview')
def trajectory_preview():
    profile_id = request.args['temperatureprofile']
    _, trajectory = load_profile(profile_id)

    time, target_temperature = zip(*trajectory)
    time = [t / 60.0 for t in time]  # convert to minutes

    data = pd.DataFrame({
        'time': time,
        'temperature': target_temperature
    })
    return jsonify(json.loads(data.to_json(orient='records')))
