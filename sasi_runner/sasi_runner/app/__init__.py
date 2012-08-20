import sasi_runner.flask_config as flask_config
from sasi_runner.config import config as sr_config
import db

from flask import Flask, render_template
import os
import logging


app = Flask(__name__)
app.config.from_object(flask_config)

file_handler = logging.FileHandler(sr_config['LOGFILE'])
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
app.logger.addHandler(file_handler) 

@app.errorhandler(404)
def not_found(error):
	return '404 badness', 404

@app.teardown_request
def shutdown_session(exception=None):
	db.session.remove()

from sasi_runner.app.sasi_model_config.views import bp as config_bp
app.register_blueprint(config_bp)
