import sys
sys.path.insert(0, '..')

from app import app
from werkzeug.serving import run_simple
import flask_config

class PrefixFix(object):
	def __init__(self, app, script_name):
		self.app = app
		self.script_name = script_name

	def __call__(self, environ, start_response):
		path_info = environ.get('PATH_INFO', '')
		environ['SCRIPT_NAME'] = self.script_name
		if path_info.startswith(self.script_name):
			environ['PATH_INFO'] = path_info[len(self.script_name):]
		return self.app(environ, start_response)

prefix = flask_config.APPLICATION_ROOT
app.wsgi_app = PrefixFix(app.wsgi_app, '/' + prefix)
app.config['APPLICATION_ROOT'] = prefix
app.config['DEBUG'] = True
run_simple('localhost', 5001, app.wsgi_app, use_reloader=True, use_debugger=True)