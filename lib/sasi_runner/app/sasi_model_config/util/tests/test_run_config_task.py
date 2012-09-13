from sasi_runner.app.test.db_testcase import DBTestCase
import sasi_runner.app.db as db
from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
import sasi_runner.app.sasi_model_config.util.tests.config_setup as config_setup
import sasi_runner.app.sasi_model_config.util.run_config_task as rct
import sys
import os
import unittest
import time
import tempfile


class RunConfigTaskTest(DBTestCase):

    def get_engine_uri(self):
        hndl, dbfile = tempfile.mkstemp(suffix=".tst.sqlite")
        return  'sqlite:///%s?check_same_thread=False' % dbfile

    def setUp(self):
        super(RunConfigTaskTest, self).setUp()
        db.clear_db(bind=self.connection)
        db.init_db(bind=self.connection)

    def test_run_config_task(self):
        config = config_setup.generate_config()
        db.session.add(config)
        db.session.commit()
        task = rct.RunConfigTask(
            config_id=config.id, 
            output_format='georefine'
        )
        task.call()

if __name__ == '__main__':
    unittest.main()
