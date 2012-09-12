import pyspatialite
import sys
sys.modules['pysqlite2'] = pyspatialite
import unittest
from sasi_runner.app import app
from sasi_runner.app import db
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

class DBTestCase(unittest.TestCase):

    def get_engine_uri(self):
        return 'sqlite://'

    def setUp(self):
        self.engine = create_engine(self.get_engine_uri())
        self.connection = self.engine.connect()
        self.connection.execute("SELECT InitSpatialMetaData()") 
        self.trans = self.connection.begin()
        db.session = scoped_session(sessionmaker(bind=self.connection))

        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        self.trans.rollback()
        db.session.close

if __name__ == '__main__':
    unittest.main()
