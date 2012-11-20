import unittest
from sasi_runner.tasks.run_sasi_task import RunSasiTask
from sasi_runner.app.test.db_testcase import DBTestCase
import os
import logging

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


this_dir = os.path.dirname(os.path.abspath(__file__))


class RunSasiTaskTestCase(DBTestCase):
    def test_run_sasi_task(self):

        task = RunSasiTask(
            input_file="%s/../test_data/bundle_actual_nominal.zip" % this_dir, 
            logger=logger,
            config={
                'ingest': {
                    'sections': {
                        'habitats': {
                            #'limit': 1000,
                        },
                        'grid': {
                            #'limit': 1000,
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
