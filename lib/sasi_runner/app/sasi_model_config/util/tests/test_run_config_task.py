from sasi_runner.app.test.db_testcase import DBTestCase
from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
import sasi_runner.app.sasi_model_config.util.tests.config_setup as config_setup
import sasi_runner.app.sasi_model_config.util.run_config_task as rct
import os
import unittest


class RunConfigTaskTest(DBTestCase):

    def test_run_config_task(self):
        config = config_setup.generate_config()
        task = rct.get_run_config_task(config)
        task.run()

if __name__ == '__main__':
    unittest.main()
