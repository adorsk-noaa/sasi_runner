import unittest
from sasi_runner.app.test.db_testcase import DBTestCase
from flask import json
from StringIO import StringIO

class SASIFileTest(DBTestCase):

    def setUp(self):
        super(SASIFileTest, self).setUp()
        self.base_path = '/sasi_file'
        self.setUpTables()

    def testUploadCategoryFileTest(self):
        category = "test_category"
        path = "%s/category/%s/" % (self.base_path, category)
        r = self.client.post(path, data={'sasi_file': (StringIO('content'),
                                                          'my_file.txt')})

    def testGetCategoryFiles(self):
        category = "test_category"
        path = "%s/category/%s/" % (self.base_path, category)
        for i in range(0,3):
            self.client.post(path, data={
                'sasi_file': (StringIO("file_%s content" % i), 
                              "file_%s.txt" % i)
            })
        r = self.client.get(path)
        files = json.loads(r.data)

    def testGetFileData(self):
        category = "test_category"
        path = "%s/category/%s/" % (self.base_path, category)
        r = self.client.post(path, data={'sasi_file': (StringIO('content'),
                                                          'my_file.txt')})
        uploaded_file_data = json.loads(r.data)
        path = "/%s/%s/" % (self.base_path, uploaded_file_data['id'])

        r = self.client.get(path)
        file_data = json.loads(r.data)


if __name__ == '__main__':
    unittest.main()
