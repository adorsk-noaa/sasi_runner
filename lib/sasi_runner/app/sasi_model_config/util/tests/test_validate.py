from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
import sasi_runner.app.sasi_model_config.util.validation as validation
import sasi_runner.app.sasi_model_config.util.config_generator as config_generator
import os
import unittest


class SASIModelConfigValidationTest(unittest.TestCase):

    def test_validate_config(self):
        config = config_generator.generate_config()
        validation.validate_config(config)

if __name__ == '__main__':
    unittest.main()
