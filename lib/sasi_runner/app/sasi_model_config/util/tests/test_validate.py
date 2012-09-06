from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
import sasi_runner.app.sasi_model_config.util.validation as validation
import sasi_runner.app.sasi_model_config.util.tests.config_setup as config_setup
import os
import unittest


class SASIModelConfigValidationTest(unittest.TestCase):

    def setUp(self):
        self.configs = {}
        self.configs['config_1'] = config_setup.setUp_config_1()

    def test_validate_config(self):
        validation.validate_config(self.configs['config_1'])

if __name__ == '__main__':
    unittest.main()
