import pyspatialite
import sys
sys.modules['pysqlite2'] = pyspatialite
import unittest
from sqlalchemy import (create_engine, MetaData)
from sqlalchemy.orm import (scoped_session, sessionmaker)


class DBTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        self.connection = self.engine.connect()
        self.session = scoped_session(sessionmaker(bind=self.connection))
        self.connection.execute("SELECT InitSpatialMetaData()") 

if __name__ == '__main__':
    unittest.main()
