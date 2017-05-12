import configparser
import subprocess

from flask import Flask
from flask import render_template, jsonify, Response, request
from flask_bootstrap import Bootstrap

import update.releases as releases

app = Flask(__name__)
Bootstrap(app)


@app.route('/')
def index():
    version = releases.current_version()
    versions = releases.list_versions()
    return render_template('update.html', current_version=version, releases=versions)


@app.route('/update')
def execute():
    try:
        releases.update_to_latest()
        response = {
            'returncode': 0,
            'stdout': '',
            'stderr': ''
        }
    except subprocess.CalledProcessError as proc:
        response = {
            'returncode': proc.returncode,
            'stdout': proc.stdout,
            'stderr': proc.stderr
        }
    return jsonify(response)


@app.route('/revert')
def revert():
    version = request.args['version']

    try:
        releases.revert(version)
        response = {
            'returncode': 0,
            'stdout': '',
            'stderr': ''
        }
    except subprocess.CalledProcessError as proc:
        response = {
            'returncode': proc.returncode,
            'stdout': proc.stdout,
            'stderr': proc.stderr
        }

    return jsonify(response)


@app.route('/reboot', methods=['POST'])
def reboot():
    subprocess.run(['sudo', 'reboot'])
    return Response()


def main(config_filename):
    try:
        config_parser = configparser.ConfigParser()
        config_parser.read(config_filename)
        http_port = config_parser.getint('update', 'http_port')
    except configparser.NoSectionError:
        http_port = 8888
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    app.run(host='0.0.0.0', port=http_port, debug=False)
