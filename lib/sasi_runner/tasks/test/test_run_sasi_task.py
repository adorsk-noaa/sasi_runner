import pyspatialite
import sys
sys.modules['pysqlite2'] = pyspatialite
import unittest
from sasi_runner.tasks.run_sasi_task import RunSasiTask
import os
import logging
from sqlalchemy import create_engine

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


this_dir = os.path.dirname(os.path.abspath(__file__))


class RunSasiTaskTestCase(unittest.TestCase):
    def test_run_sasi_task(self):

        def get_connection():
            engine = create_engine('sqlite://')
            con = engine.connect()
            con.execute('SELECT InitSpatialMetadata()')
            return con

        task = RunSasiTask(
            input_path="%s/../test_data/reduced_test_data" % this_dir, 
            logger=logger,
            get_connection=get_connection,
            config={
                'ingest': {
                    'sections': {
                        'gears': {
                            'limit': 1,
                        },
                        'habitats': {
                            #'limit': 1000,
                        },
                        'grid': {
                            #'limit': 100,
                        }
                    }
                },
                'run_model': {
                    'commit_interval': 1000,
                }
            }
        )
        task.call()

if __name__ == '__main__':
    unittest.main()
