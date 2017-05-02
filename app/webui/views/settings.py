import os

from flask import Blueprint, render_template, send_file, request, redirect, url_for, current_app
from werkzeug.utils import secure_filename

from webui.profiles import load_profiles, delete_profile

settings = Blueprint(
    'settings', __name__,
    url_prefix='/settings',
    template_folder='templates',
    static_folder='static')


@settings.route('/')
def index():
    profiles = [(profile.profile_id, profile.name) for profile in load_profiles().values()]
    return render_template('settings.html', profiles=profiles)


@settings.route('/profile/import', methods=['POST'])
def profile_import():
    file = request.files['filename']
    filename = secure_filename(file.filename)
    file.save(os.path.join(current_app.config['PROFILE_DIRECTORY'], filename))
    return redirect(url_for('settings.index'))


@settings.route('/profile/delete', methods=['POST'])
def profile_delete():
    profile_id = request.form['temperatureprofile']
    delete_profile(profile_id)
    return redirect(url_for('settings.index'))


@settings.route('/profile/export', methods=['POST'])
def profile_export():
    profile_id = request.form['temperatureprofile']
    return send_file('temperature-profiles/{}.xlsx'.format(profile_id), as_attachment=True)


@settings.route('/Profilvorlage.xlsx')
def get_profile_template():
    return send_file('Profilvorlage.xlsx', as_attachment=True)
