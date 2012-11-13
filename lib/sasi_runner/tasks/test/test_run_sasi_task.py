import unittest
from sasi_runner.tasks.run_sasi_task import RunSasiTask
import os


this_dir = os.path.dirname(os.path.abspath(__file__))

class RunSasiTaskTestCase(unittest.TestCase):
    def test_run_sasi_task(self):
        task = RunSasiTask(input_file="%s/../test_data/bundle.zip" % this_dir)
        task.call()

if __name__ == '__main__':
    unittest.main()
