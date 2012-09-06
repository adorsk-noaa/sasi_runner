import unittest
from sasi_runner.util.sa.tests.db_testcase import DBTestCase
from sasi_runner.util.sasi_data.ingest.sasi_ingestor import SASI_Ingestor
from sasi_runner.util.sasi_data.tests.generate_test_data import generate_data
from sasi_runner.util.sasi_data.dao.sasi_sa_dao import SASI_SqlAlchemyDAO
import shutil


class SASI_Ingestor_TestCase(DBTestCase):
    def setUp(self):
        DBTestCase.setUp(self)
        self.data_dir = generate_data()

    def tearDown(self):
        if self.data_dir:
            shutil.rmtree(self.data_dir)
        DBTestCase.tearDown(self)

    def test_sasi_ingestor(self):
        dao = SASI_SqlAlchemyDAO(session=self.session)
        sasi_ingestor = SASI_Ingestor(dao=dao)
        sasi_ingestor.ingest(data_dir=self.data_dir)

if __name__ == '__main__':
    unittest.main()
