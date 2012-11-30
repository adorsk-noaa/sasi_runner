import unittest
from test_run_sasi_task import RunSasiTaskTestCommon
from sqlalchemy import create_engine
import os
import shutil
import logging


class JyRunSasiTaskTestCase(unittest.TestCase, RunSasiTaskTestCommon):

    def __init__(self, *args, **kwargs):
        RunSasiTaskTestCommon.__init__(self, *args, **kwargs)
        unittest.TestCase.__init__(self, *args, **kwargs)

    def get_input_path(self):
        this_dir = os.path.dirname(os.path.abspath(__file__))
        return "%s/../test_data/new_test_data" % this_dir
        #return "%s/../test_data/reduced_test_data" % this_dir
        #return "%s/../test_data/mock_data" % this_dir

    @staticmethod
    def get_connection(*args):
        #if os.path.exists('/tmp/foo'):
            #shutil.rmtree('/tmp/foo')
        #os.mkdir('/tmp/foo')
        #engine = create_engine('h2+zxjdbc:////tmp/foo/foo')
        engine = create_engine('h2+zxjdbc:///mem:')
        con = engine.connect()
        javaCon = con.connection.__connection__
        from geodb.GeoDB import InitGeoDB
        InitGeoDB(javaCon)
        return con

    def get_config(self):
        return {
            'ingest': {
                'sections': {
                    'gears': {
                        #'limit': 1,
                    },
                    'habitats': {
                        #'limit': 1,
                    },
                    'grid': {
                        #'limit': 1,
                    }
                }
            },
            'run_model': {
                'commit_interval': 1000,
            }
        }

if __name__ == '__main__':
    unittest.main()
