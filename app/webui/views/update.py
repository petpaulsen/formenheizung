import subprocess

from flask import Blueprint, render_template, jsonify, Response, request

from webui.models.update import current_release, list_releases

update = Blueprint(
    'update', __name__,
    url_prefix='/update',
    template_folder='templates',
    static_folder='static')


@update.route('/')
def index():
    current_version = current_release()
    if current_version is None:
        current_version = '???'
    releases = list_releases()
    return render_template('update.html', current_version=current_version, releases=releases)


@update.route('/update')
def execute():
    import time
    time.sleep(3)

    proc = subprocess.run(['bash', 'bin/update.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    response = {
        'returncode': proc.returncode,
        'stdout': proc.stdout,
        'stderr': proc.stderr
    }
    return jsonify(response)


@update.route('/revert')
def revert():
    version = request.args['version']

    proc = subprocess.run(
        ['bash', 'bin/revert.sh', version],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
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
