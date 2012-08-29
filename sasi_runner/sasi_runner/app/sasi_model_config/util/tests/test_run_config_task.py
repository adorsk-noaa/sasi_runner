from sasi_runner.app.test.db_testcase import DBTestCase
from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
import sasi_runner.app.sasi_model_config.util.tests.config_setup as config_setup
import sasi_runner.app.sasi_model_config.util.run_config_task as rct
import os
import unittest


class RunConfigTaskTest(DBTestCase):

    def setUp(self):
        super(RunConfigTaskTest, self).setUp()
        self.configs = {}
        self.configs['config_1'] = config_setup.setUp_config_1()

    def test_run_config_task(self):
        task = rct.get_run_config_task(self.configs['config_1'])
        task.run()

if __name__ == '__main__':
    unittest.main()
