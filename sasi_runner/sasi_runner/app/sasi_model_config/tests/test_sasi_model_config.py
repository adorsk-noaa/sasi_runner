import unittest
import sasi_runner.app as sr
from flask import json

class SASIModelConfigTest(unittest.TestCase):

    def setUp(self):
        sr.app.config['TESTING'] = True
        self.app = sr.app.test_client()
        self.base_path = '/ks'

if __name__ == '__main__':
    unittest.main()
