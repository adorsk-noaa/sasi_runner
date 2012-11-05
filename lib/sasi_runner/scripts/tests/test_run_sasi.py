from sasi_runner.scripts import run_sasi
from sasi_runner.app.test.db_testcase import DBTestCase
import sasi_runner.app.db as db
import sasi_runner.app.sasi_model_config.util.config_generator as config_generator
import unittest
import tempfile


class RunSasiTest(DBTestCase):

    def test_run_sasi(self):
        config = config_generator.generate_config(bundled=False)

        input_files = {}
        for category, input_file in config.files.items():
            input_files[category] = input_file.path

        hndl, output_file = tempfile.mkstemp(prefix="trs.", suffix=".tar.gz")

        output_format="georefine"

        run_sasi.run_sasi(
            input_files=input_files,
            output_file=output_file,
            output_format=output_format
        )


if __name__ == '__main__':
    unittest.main()
