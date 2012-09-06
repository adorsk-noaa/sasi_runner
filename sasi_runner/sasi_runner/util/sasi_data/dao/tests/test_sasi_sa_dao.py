import unittest
from sasi_runner.util.sa.tests.db_testcase import DBTestCase
from sasi_runner.util.sasi_data.dao.sasi_sa_dao import SASI_SqlAlchemyDAO


class SASI_SqlAlchemyDAOTestCase(DBTestCase):
    def setUp(self):
        DBTestCase.setUp(self)
        self.dao = SASI_SqlAlchemyDAO(session=self.session)

if __name__ == '__main__':
    unittest.main()
