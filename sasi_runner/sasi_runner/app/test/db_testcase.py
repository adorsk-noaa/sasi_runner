import unittest
from sasi_runner.app import app
from sasi_runner.app import db
from sqlalchemy.orm import scoped_session, sessionmaker

class DBTestCase(unittest.TestCase):

    def setUp(self):
        connection = db.engine.connect()
        self.trans = connection.begin()
        db.session = scoped_session(sessionmaker(bind=connection))

        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        self.trans.rollback()
        db.session.close

if __name__ == '__main__':
    unittest.main()
