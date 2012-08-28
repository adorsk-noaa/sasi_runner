from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
import sasi_runner.app.sasi_model_config.util as smc_util
import os
import unittest

base_dir = os.path.dirname(os.path.abspath(__file__))
base_data_dir = os.path.join(base_dir, "test_data")

class SASIModelConfigValidationTest(unittest.TestCase):

    seq = 0

    def get_id(self):
        self.seq += 1
        return self.seq

    def setUp(self):
        file_counter = 1
        self.configs = {}
        self.configs['config_1'] = self.setUp_config_1()

    def setUp_config_1(self):
        data_dir = os.path.join(base_data_dir, "config_1")
        config = SASIModelConfig(
            id=self.get_id(),
            title="config 1"
        )

        # Setup file sections.
        for section in [
            'substrates', 
            'features', 
            'gears',
            'va',
            'habitats',
            'grid',
            'parameters'
        ]:
            setattr(config, section, SASIFile(
                id=self.get_id(),
                path=os.path.join(data_dir, section + ".zip"),
                filename=section + ".zip",
                category=section,
                size=12345,
                created=None
            ))

        return config

    def test_validate_config(self):
        smc_util.validate_config(self.configs['config_1'])

if __name__ == '__main__':
    unittest.main()
