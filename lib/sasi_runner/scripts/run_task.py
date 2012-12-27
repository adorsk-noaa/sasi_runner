from sasi_runner.tasks.run_sasi_task import RunSasiTask
from sqlalchemy import create_engine
import logging
import argparse
import platform
import sys
import tempfile
import shutil
import os


argparser = argparse.ArgumentParser()
argparser.add_argument('input')
argparser.add_argument('--db-uri')

args = argparser.parse_args()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

db_dir = None

def get_connection():
    db_uri = args.db_uri
    if not db_uri:
        db_dir = tempfile.mkdtemp(prefix="rst.db.")
        db_file = os.path.join(db_dir, "db")
        if platform.system() == 'Java':
            db_uri = 'h2+zxjdbc:///%s' % db_file
        else:
            db_uri = 'sqlite:///%s.sqlite' % db_file
    engine = create_engine(db_uri)
    con = engine.connect()
    return con

print db_dir

task = RunSasiTask(
    input_path=args.input,
    logger=logger,
    get_connection=get_connection,
)
task.call()

if db_dir:
    shutil.rmtree(db_dir)
