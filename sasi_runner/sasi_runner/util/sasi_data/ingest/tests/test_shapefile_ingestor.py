import unittest
from sasi_runner.util.sa.tests.db_testcase import DBTestCase
from sasi_runner.util.sasi_data.ingest.shapefile_ingestor import (
    Shapefile_Ingestor)
from sa_dao.orm_dao import ORM_DAO
import shapefile
from sqlalchemy import Table, Column, Integer, String
from geoalchemy import GeometryColumn, MultiPolygon, GeometryDDL
from sqlalchemy.ext.declarative import declarative_base
import tempfile
import os
import time


class Shapefile_Ingestor_TestCase(DBTestCase):
    def setUp(self):
        DBTestCase.setUp(self)

    def test_shapefile_ingestor(self):
        Base = declarative_base()

        class TestClass(Base):
            __tablename__ = 'testclass'
            id = Column(Integer, primary_key=True)
            attr1 = Column(Integer) 
            attr2 = Column(String)
            geom = GeometryColumn(MultiPolygon(2))
        GeometryDDL(TestClass.__table__)
        schema = {
            'sources': {
                'TestClass': TestClass
            }
        }

        Base.metadata.create_all(self.connection)

        dao = ORM_DAO(session=self.session, schema=schema)

        shp_dir = tempfile.mkdtemp()
        shp_file = os.path.join(shp_dir, "test.shp")
        w = shapefile.Writer()
        w.shapeType = shapefile.POLYGON
        w.field('S_ATTR1')
        w.field('S_ATTR2', 'C', 40)
        for i in range(5):
            parts = [
                [i, i], [i, i+1], [i+1, i+1], [i+1, i]
            ]
            parts.append(parts[0])
            w.poly([parts])
            w.record(i, "s_attr2_%s" % i)
        w.save(shp_file)

        mappings = [
            {
                'source': 'S_ATTR1', 
                'target': 'attr1',
                'processor': lambda value: int(value) * 10
            },

            {
                'source': 'S_ATTR2', 
                'target': 'attr2',
            },
        ]

        shp_ingestor = Shapefile_Ingestor(
            dao=dao,
            shp_file=shp_file, 
            clazz=TestClass, 
            mappings=mappings
        )
        shp_ingestor.ingest()
        result = dao.query({
            'SELECT': ['{{TestClass}}']
        })

        for r in result.all():
            print r.attr1, r.attr2, dao.session.scalar(r.geom.wkt)


if __name__ == '__main__':
    unittest.main()
