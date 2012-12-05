from sasi_runner.tasks.run_sasi_task import RunSasiTask
from sqlalchemy import create_engine
import logging
import argparse
import platform
import sys


argparser = argparse.ArgumentParser()
argparser.add_argument('input')
argparser.add_argument('--db-uri', default='sqlite://')

args = argparser.parse_args()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

def get_connection():
    if platform.system() == 'Java':
        engine = create_engine(args.db_uri)
        con = engine.connect()
        javaCon = con.connection.__connection__
        from geodb.GeoDB import InitGeoDB
        InitGeoDB(javaCon)
        return con
    else:
        import pyspatialite
        sys.modules['pysqlite2'] = pyspatialite
        engine = create_engine(args.db_uri)
        con = engine.connect()
        con.execute('SELECT InitSpatialMetadata()')
        return con

task = RunSasiTask(
    input_path=args.input,
    logger=logger,
    get_connection=get_connection,
)
task.call()
