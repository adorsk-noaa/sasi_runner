from sasi_runner.config import config as sr_config

DEBUG = False

SQLALCHEMY_DATABASE_URI = sr_config['DB_URI']

SECRET_KEY = sr_config.get('SECRET_KEY', 'secretawesome')

UPLOAD_FOLDER = '/tmp'

ALLOWED_EXTENSIONS = set(['txt'])

APPLICATION_ROOT = "sasi_runner"



