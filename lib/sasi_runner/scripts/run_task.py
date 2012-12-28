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
argparser.add_argument('--run-batch-size', '-rbs', default='auto')
argparser.add_argument('--write-batch-size', '-wbs', default='auto')

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

# Run batch size.
try:
    run_batch_size = float(args.run_batch_size)
except:
    run_batch_size = args.run_batch_size

# Write batch size.
try:
    write_batch_size = float(args.write_batch_size)
except:
    write_batch_size = args.write_batch_size

task = RunSasiTask(
    input_path=args.input,
    logger=logger,
    get_connection=get_connection,
    config={
        'ingest': {
            'sections': {
                'grid': {
                    'limit': 1e2
                },
                'habitats': {
                    'limit': 1e2
                },
            }
        },
        'run_model': {
            'run': {
                'batch_size': run_batch_size,
            },
        },
        'output': {
            'batch_size': write_batch_size,
        },
    }
)
task.call()

if db_dir:
    shutil.rmtree(db_dir)
