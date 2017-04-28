import json

import pandas as pd
from flask import Blueprint, render_template, jsonify, request, current_app

from webui.profiles import load_profiles

plot = Blueprint(
    'plot', __name__,
    url_prefix='/plot',
    template_folder='templates',
    static_folder='static')


@plot.route('/')
def index():
    profiles = [(profile.profile_id, profile.name) for profile in load_profiles().values()]
    return render_template('plot.html', profiles=profiles)


@plot.route('/trajectory-preview')
def trajectory_preview():
    profile_id = request.args['temperatureprofile']
    profile = load_profiles()[profile_id]

    time, target_temperature = zip(*profile.trajectory)

    data = pd.DataFrame({
        'time': time,
        'temperature': target_temperature
    })
    return jsonify(json.loads(data.to_json(orient='records')))
