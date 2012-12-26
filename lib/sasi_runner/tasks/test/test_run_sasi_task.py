import sys
import unittest
from sasi_runner.tasks.run_sasi_task import RunSasiTask
import os
import logging
from sqlalchemy import create_engine
import argparse
from sasi_data.util.data_generators import generate_data_dir
import shutil


class RunSasiTaskTestCommon(object):
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger('test')
        self.logger.addHandler(logging.StreamHandler())
        self.logger.setLevel(logging.DEBUG)

    @staticmethod
    def get_connection():
        pass

    def get_input_path(self):
        this_dir = os.path.dirname(os.path.abspath(__file__))
        #return "%s/../test_data/reduced_test_data" % this_dir
        return "%s/../test_data/new_test_data" % this_dir

    def get_config(self):
        return {
            'ingest': {
                'sections': {
                    'gears': {
                        #'limit': 1,
                    },
                    'habitats': {
                        #'limit': 1000,
                    },
                    'grid': {
                        #'limit': 100,
                    }
                }
            },
            #'run_model': {
                #'batch_size': 100,
            #}
        }

    def test_run_sasi_task(self):
        task = RunSasiTask(
            input_path=self.data_dir,
            logger=self.logger,
            get_connection=self.get_connection,
            config=self.get_config(),
            max_mem=10e9,
        )
        task.call()

class PyRunSasiTaskTestCase(unittest.TestCase, RunSasiTaskTestCommon):
    def __init__(self, *args, **kwargs):
        RunSasiTaskTestCommon.__init__(self, *args, **kwargs)
        unittest.TestCase.__init__(self, *args, **kwargs)

    def setUp(self):
        self.data_dir = generate_data_dir(effort_model='nominal')
    def tearDown(self):
        if hasattr(self, 'data_dir') and self.data_dir.startswith('/tmp'):
            shutil.rmtree(self.data_dir)

    @staticmethod
    def get_connection():
        import pyspatialite
        sys.modules['pysqlite2'] = pyspatialite
        engine = create_engine('sqlite://')
        con = engine.connect()
        con.execute('SELECT InitSpatialMetadata()')
        return con

if __name__ == '__main__':
    unittest.main()
