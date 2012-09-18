import sasi_runner.flask_config as flask_config
from sasi_runner.config import config as sr_config
from sasi_runner.app import db as db

from flask import Flask, render_template
from flaskext.uploads import configure_uploads
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

from sasi_runner.app.sasi_file.views import bp as sasi_file_bp
from sasi_runner.app.sasi_file.views import upload_sets as sasi_file_upload_sets
app.register_blueprint(sasi_file_bp)
configure_uploads(app, sasi_file_upload_sets)

from sasi_runner.app.tasks.views import bp as tasks_bp
app.register_blueprint(tasks_bp)

from sasi_runner.app.sasi_result.views import bp as result_bp
app.register_blueprint(result_bp)
