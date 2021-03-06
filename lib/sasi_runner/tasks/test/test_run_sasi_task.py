import sys
import unittest
from sasi_runner.tasks.run_sasi_task import RunSasiTask
import os
import logging
from sqlalchemy import create_engine
import argparse
from sasi_data.util.data_generators import generate_data_dir
import shutil
import platform


class RunSasiTaskTestCase(unittest.TestCase):

    def tearDown(self):
        if hasattr(self, 'data_dir') and self.data_dir.startswith('/tmp'):
            shutil.rmtree(self.data_dir)

    def test_run_sasi_task(self):
        self.data_dir = generate_data_dir(effort_model='nominal')

        def get_connection():
            if platform.system() == 'Java':
                db_uri = 'h2+zxjdbc:///mem:'
            else:
                db_uri = 'sqlite://'
            engine = create_engine(db_uri)
            con = engine.connect()
            return con

        logger = logging.getLogger('test')
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

        task = RunSasiTask(
            input_path=self.data_dir,
            get_connection=get_connection,
            logger=logger,
            config={
                #'result_fields': ['gear_id', 'substrate_id'],
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
                'run_model': {
                    'run': {
                        'batch_size': 'auto',
                    }
                },
            }
        )
        task.call()

if __name__ == '__main__':
    unittest.main()
