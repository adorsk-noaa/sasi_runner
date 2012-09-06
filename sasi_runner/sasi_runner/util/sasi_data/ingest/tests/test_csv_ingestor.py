import unittest
from sasi_runner.util.sa.tests.db_testcase import DBTestCase
from sasi_runner.util.sasi_data.ingest.csv_ingestor import CSV_Ingestor
from sa_dao.orm_dao import ORM_DAO
from StringIO import StringIO
import csv
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


class CSV_Ingestor_TestCase(DBTestCase):
    def setUp(self):
        DBTestCase.setUp(self)

    def test_csv_ingestor(self):
        Base = declarative_base()

        class TestClass(Base):
            __tablename__ = 'testclass'
            id = Column(Integer, primary_key=True)
            attr1 = Column(Integer) 
            attr2 = Column(String)
        Base.metadata.create_all(self.connection)
        schema = {
            'sources': {
                'TestClass': TestClass
            }
        }

        dao = ORM_DAO(session=self.session, schema=schema)

        csv_data = StringIO()
        writer = csv.DictWriter(csv_data, fieldnames=['s_attr1', 's_attr2'])
        writer.writeheader()
        for i in range(5):
            record = {
                's_attr1': i,
                's_attr2': "s_attr2_%s" % i,
            }
            writer.writerow(record)
        csv_file = StringIO(csv_data.getvalue())

        mappings = [
            {
                'source': 's_attr1', 
                'target': 'attr1',
                'processor': lambda value: int(value) * 10
            },

            {
                'source': 's_attr2', 
                'target': 'attr2',
            },
        ]

        csv_ingestor = CSV_Ingestor(
            dao=dao,
            csv_file=csv_file, 
            clazz=TestClass, 
            mappings=mappings
        )
        csv_ingestor.ingest()
        result = dao.query({
            'SELECT': ['{{TestClass}}']
        })

if __name__ == '__main__':
    unittest.main()
