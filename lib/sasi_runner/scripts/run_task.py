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
argparser.add_argument('--batch-size', '-b', type=int, default=100)

args = argparser.parse_args()

logger = logging.getLogger('run_task')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

#logging.getLogger('sqlalchemy.engine').addHandler(logging.StreamHandler())
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

db_dir = None

def get_connection():
    db_uri = args.db_uri
    if not db_uri:
        db_dir = tempfile.mkdtemp(prefix="rst.db.")
        db_file = os.path.join(db_dir, "db")
        if platform.system() == 'Java':
            cache_size = 64 * 1024
            pragmas = 'LOG=0;CACHE_SIZE=%s;LOCK_MODE=0;UNDO_LOG=0' % cache_size
            db_uri = 'h2+zxjdbc:///%s;%s' % (db_file, pragmas)
        else:
            db_uri = 'sqlite:///%s.sqlite' % db_file
    engine = create_engine(db_uri)
    con = engine.connect()
    return con

task = RunSasiTask(
    input_path=args.input,
    logger=logger,
    get_connection=get_connection,
    config={
        'run_model': {
            'batch_size': args.batch_size
        },
        'ingest': {
            'sections': {
                'grid': {
                    'limit': 1e3
                },
                'habitats': {
                    'limit': None
                },
            }
        }
    }
)
task.call()

if db_dir:
    shutil.rmtree(db_dir)
