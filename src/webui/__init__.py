import configparser
import logging

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View

from .views.controller import controller
from .views.plot import plot, index as plot_index
from .views.settings import settings
from .views.update import update

app = Flask(__name__)
Bootstrap(app)
app.register_blueprint(plot)
app.register_blueprint(controller)
app.register_blueprint(settings)
app.register_blueprint(update)

topbar = Navbar(
    '',
    View('Steuerung', 'index'),
    View('Einstellungen', 'settings.index'),
    View('Aktualisierung', 'update.index')
)
nav = Nav()
nav.register_element('top', topbar)
nav.init_app(app)


@app.route('/')
def index():
    return plot_index()


@app.errorhandler(500)
def internal_error(exception):
    app.logger.error(exception)


class Config:
    def __init__(self, controller_port):
        self.CONTROLLER_PORT = controller_port


def main(config_filename, controller_port_=None, http_port=None, log_filename=None):
    config_parser = configparser.ConfigParser()
    config_parser.read(config_filename)
    if controller_port_ is not None:
        controller_port = controller_port_
    else:
        controller_port = config_parser.getint('controller', 'network_port')
    if http_port is None:
        http_port = config_parser.getint('webui', 'http_port')

    if log_filename is not None:
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    app.config.from_object(Config(controller_port))
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['PROFILE_DIRECTORY'] = 'src/webui/temperature-profiles'
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    app.run(host='0.0.0.0', port=http_port, debug=False)
