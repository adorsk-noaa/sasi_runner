from sasi_runner.app.test.db_testcase import DBTestCase
import sasi_runner.app.db as db
from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
import sasi_runner.app.sasi_model_config.util.config_generator as config_generator
import sasi_runner.app.sasi_model_config.util.run_config_task as rct
import sys
import os
import unittest
import time
import tempfile


class RunConfigTaskTest(DBTestCase):

    # Note: can't use sqlite for this test, due to db locking
    # for multi-threading.
    def get_engine_uri(self):
        return 'postgresql://test:test@localhost/gis_test'
    
    def spatializeDB(self): pass

    def test_run_config_task(self):
        config = config_generator.generate_config()
        db.session.add(config)
        db.session.commit()
        task = rct.get_run_config_task(
            config_id=config.id, 
            output_format='georefine'
        )
        task.call()

if __name__ == '__main__':
    unittest.main()
