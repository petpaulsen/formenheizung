import subprocess

from flask import Blueprint, render_template, jsonify, Response

update = Blueprint(
    'update', __name__,
    url_prefix='/update',
    template_folder='templates',
    static_folder='static')


@update.route('/')
def index():
    proc = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, encoding='utf-8')
    if proc.returncode == 0:
        current_version = proc.stdout
    else:
        current_version = '???'
    return render_template('update.html', current_version=current_version)


@update.route('/execute')
def execute():
    proc = subprocess.run(['bash', 'bin/update.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    response = {
        'returncode': proc.returncode,
        'stdout': proc.stdout,
        'stderr': proc.stderr
    }
    return jsonify(response)


@update.route('/reboot', methods=['POST'])
def reboot():
    subprocess.run(['sudo', 'reboot'])
    return Response()
