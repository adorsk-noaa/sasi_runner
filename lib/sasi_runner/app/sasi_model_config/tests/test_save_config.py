from sasi_runner.app.test.db_testcase import DBTestCase
from sasi_runner.app import db
from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_model_config.models import SASIModelConfig

from flask import json, url_for
from StringIO import StringIO
import unittest


class SaveConfigTest(DBTestCase):

    def setUp(self):
        super(SaveConfigTest, self).setUp()
        self.base_path = '/config'

        # Create file models.
        self.file_attrs = [
            'substrates',
            'features',
            'gears',
            'habitats',
            'grid',
            'va',
            'model_parameters',
            'map_layers',
            'fishing_efforts'
        ]
        self.file_models = {}
        for attr in self.file_attrs:
            self.file_models[attr] = SASIFile(filename=(attr+".txt"))

        db.session.add_all(self.file_models.values())
        db.session.commit()

    def testCreateConfig(self):
        path = "%s/" % (self.base_path)
        data = {'title': "fish"}
        for attr, sasi_file in self.file_models.items():
            data[attr] = sasi_file.id
        r = self.client.post(path, data=data)

    def testUpdateConfig(self):
        config = SASIModelConfig(title="smifto")
        db.session.add(config)
        db.session.commit()
        path = "%s%s/" % (self.base_path, config.id)
        data = {'title': 'blorgas'}
        for attr, sasi_file in self.file_models.items():
            data[attr] = sasi_file.id
        r = self.client.post(path, data=data)

if __name__ == '__main__':
    unittest.main()
