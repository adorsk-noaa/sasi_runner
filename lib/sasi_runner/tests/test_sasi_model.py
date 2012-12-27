import unittest
from sasi_data.util import data_generators as dg
from sasi_data.dao.sasi_sa_dao import SASI_SqlAlchemyDAO
import sasi_data.models as models
from sasi_runner.sasi_model import SASI_Model
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import shutil
import platform
import sys
import time


class SASIModelTest(unittest.TestCase):

    @classmethod
    def setUpClass(clz):
        if platform.system() == 'Java':
            engine = create_engine('h2+zxjdbc:///mem:')
        else:
            engine = create_engine('sqlite://')
        clz.con = engine.connect()
        Session = sessionmaker(bind=clz.con)
        clz.session = Session()

    def setUp(self):
        self.data_dir = dg.generate_data_dir()

    def tearDown(self):
        if self.data_dir:
            shutil.rmtree(self.data_dir)

    def test_sasi_model(self):
        dao = SASI_SqlAlchemyDAO(session=self.session)

        FeatureCategory = dao.schema['sources']['FeatureCategory']
        feature_categories = [
            FeatureCategory(id='FC1'),
            FeatureCategory(id='FC2')
        ]
        dao.save_all(feature_categories)

        Feature = dao.schema['sources']['Feature']
        features = [
            Feature(id='F1', category='FC1'),
            Feature(id='F2', category='FC2'),
        ]
        dao.save_all(features)

        Gear = dao.schema['sources']['Gear']
        gears = [
            Gear(id='G1', min_depth=0, max_depth=1000),
            Gear(id='GTooDeep', min_depth=5000),
            Gear(id='GTooShallow', max_depth=0),
        ]
        dao.save_all(gears)

        Cell = dao.schema['sources']['Cell']
        cells = [
            Cell(
                id=0, 
                area=100.0, 
                habitat_composition={
                    ('S1', 'Low'): .5,
                    ('S1', 'High'): .5,
                },
                z=500,
            ),
        ]
        dao.save_all(cells)

        VA = dao.schema['sources']['VA']
        vas = [
            VA(
                substrate_id='S1',
                energy_id='High',
                gear_id='G1',
                feature_id='F1',
                s=1,
                r=1,
            ),
            VA(
                substrate_id='S1',
                energy_id='Low',
                gear_id='G1',
                feature_id='F1',
                s=2,
                r=2,
            ),
            VA(
                substrate_id='S1',
                energy_id='High',
                gear_id='G1',
                feature_id='F2',
                s=1,
                r=1,
            ),
            VA(
                substrate_id='S1',
                energy_id='Low',
                gear_id='G1',
                feature_id='F2',
                s=2,
                r=2,
            ),
        ]
        dao.save_all(vas)

        Effort = dao.schema['sources']['Effort']
        efforts = [
            Effort(
                time=0,
                cell_id=0,
                gear_id='G1',
                a=100.0,
                hours_fished=100.0,
                value=100.0
            ),
            # Invalid gear: should be skipped.
            Effort(
                time=0,
                cell_id=0,
                gear_id='G99',
                a=100.0,
                hours_fished=100.0,
                value=100.0
            ),
            # Out of depth limits, should be skipped.
            Effort(
                time=0,
                cell_id=0,
                gear_id='GTooDeep',
                a=100.0,
                hours_fished=100.0,
                value=100.0
            ),
            # Out of depth limits, should be skipped.
            Effort(
                time=0,
                cell_id=0,
                gear_id='GTooShallow',
                a=100.0,
                hours_fished=100.0,
                value=100.0
            ),
            Effort(
                time=1,
                cell_id=0,
                gear_id='G1',
                a=100.0,
                hours_fished=100.0,
                value=100.0
            ),
            # Test empty hours fished, value
            Effort(
                time=2,
                cell_id=0,
                gear_id='G1',
                a=100.0,
                hours_fished=None,
                value=None,
            ),
        ]
        dao.save_all(efforts)

        taus = {
            1: 1,
            2: 2,
            3: 4
        }

        omegas = {
            1: .25,
            2: .5,
            3: 1.0,
        }

        m = SASI_Model(
            t0=0,
            tf=2,
            dt=1,
            taus=taus,
            omegas=omegas,
            effort_model='realized',
            dao=dao,
        )
        m.run(batch_size=100)

        expected_result_dicts = [
            #
            # t=0
            #

            # s=1, r=1
            {
                't': 0, 
                'cell_id': 0, 
                'energy_id': 'High', 
                'substrate_id': 'S1', 
                'feature_id': 'F1', 
                'gear_id': 'G1', 
                'a': 25.0,
                'x': 0.0,
                'y': 6.25,
                'z': -6.25,
                'znet': -6.25,
                'hours_fished': 25.0,
                'value': 25.0,
            },

            # s=1, r=1
            {
                't': 0, 
                'cell_id': 0, 
                'energy_id': 'High', 
                'substrate_id': 'S1', 
                'feature_id': 'F2', 
                'gear_id': 'G1', 
                'a': 25.0,
                'x': 0.0, 
                'y': 6.25,
                'z': -6.25,
                'znet': -6.25,
                'hours_fished': 25.0,
                'value': 25.0,
            },

            # s=2, r=2
            {
                't': 0, 
                'cell_id': 0, 
                'energy_id': 'Low', 
                'substrate_id': 'S1', 
                'feature_id': 'F1', 
                'gear_id': 'G1', 
                'a': 25.0,
                'x': 0.0,
                'y': 12.5,
                'z': -12.5,
                'znet': -12.5,
                'hours_fished': 25.0,
                'value': 25.0,
            },
            # s=2, r=2
            {
                't': 0, 
                'cell_id': 0, 
                'energy_id': 'Low', 
                'substrate_id': 'S1', 
                'feature_id': 'F2', 
                'gear_id': 'G1', 
                'a': 25.0,
                'x': 0.0,
                'y': 12.5,
                'z': -12.5,
                'znet': -12.5,
                'hours_fished': 25.0,
                'value': 25.0,
            },
            #
            # t=1
            #

            # s=1, r=1
            {
                't': 1, 
                'cell_id': 0, 
                'energy_id': 'High', 
                'substrate_id': 'S1', 
                'feature_id': 'F1', 
                'gear_id': 'G1', 
                'a': 25.0,
                'x': 6.25,
                'y': 6.25,
                'z': 0.0,
                'znet': -6.25,
                'hours_fished': 25.0,
                'value': 25.0,
            },
            # s=1, r=1
            {
                't': 1, 
                'cell_id': 0, 
                'energy_id': 'High', 
                'substrate_id': 'S1', 
                'feature_id': 'F2', 
                'gear_id': 'G1', 
                'a': 25.0,
                'x': 6.25,
                'y': 6.25,
                'z': 0.0,
                'znet': -6.25,
                'hours_fished': 25.0,
                'value': 25.0,
            },
            # s=2, r=2
            {
                't': 1, 
                'cell_id': 0, 
                'energy_id': 'Low', 
                'substrate_id': 'S1', 
                'feature_id': 'F1', 
                'gear_id': 'G1', 
                'a': 25.0,
                'x': 6.25,
                'y': 12.5,
                'z': -6.25,
                'znet': -18.75,
                'hours_fished': 25.0,
                'value': 25.0,
            },
            # s=2, r=2
            {
                't': 1, 
                'cell_id': 0, 
                'energy_id': 'Low', 
                'substrate_id': 'S1', 
                'feature_id': 'F2', 
                'gear_id': 'G1', 
                'a': 25.0,
                'x': 6.25,
                'y': 12.5,
                'z': -6.25,
                'znet': -18.75,
                'hours_fished': 25.0,
                'value': 25.0,
            },
            #
            # t=2
            #

            # s=1, r=1
            {
                't': 2, 
                'cell_id': 0, 
                'energy_id': 'High', 
                'substrate_id': 'S1', 
                'feature_id': 'F1', 
                'gear_id': 'G1', 
                'a': 25.0,
                'x': 6.25,
                'y': 6.25,
                'z': 0.0,
                'znet': -6.25,
                'hours_fished': 0.0,
                'value': 0.0,
            },
            # s=1, r=1
            {
                't': 2, 
                'cell_id': 0, 
                'energy_id': 'High', 
                'substrate_id': 'S1', 
                'feature_id': 'F2', 
                'gear_id': 'G1', 
                'a': 25.0,
                'x': 6.25,
                'y': 6.25,
                'z': 0.0,
                'znet': -6.25,
                'hours_fished': 0.0,
                'value': 0.0,
            },
            # s=2, r=2
            {
                't': 2, 
                'cell_id': 0, 
                'energy_id': 'Low', 
                'substrate_id': 'S1', 
                'feature_id': 'F1', 
                'gear_id': 'G1', 
                'a': 25.0,
                'x': 12.5,
                'y': 12.5,
                'z': 0.0,
                'znet': -18.75,
                'hours_fished': 0.0,
                'value': 0.0,
            },
            # s=2, r=2
            {
                't': 2, 
                'cell_id': 0, 
                'energy_id': 'Low', 
                'substrate_id': 'S1', 
                'feature_id': 'F2', 
                'gear_id': 'G1', 
                'a': 25.0,
                'x': 12.5,
                'y': 12.5,
                'z': 0.0,
                'znet': -18.75,
                'hours_fished': 0.0,
                'value': 0.0,
            }
        ]

        actual_results = dao.query('__Result').all()
        actual_result_dicts = self.results_to_dicts(actual_results)

        self.sort_result_dicts(actual_result_dicts)
        self.sort_result_dicts(expected_result_dicts)

        self.assertEquals(len(expected_result_dicts), len(actual_result_dicts))

        for i in range(len(expected_result_dicts)):
            expected = expected_result_dicts[i]
            actual = actual_result_dicts[i]
            self.assertEquals(expected, actual)

    def results_to_dicts(self, results):
        dicts = []
        fields = [
            't', 'cell_id', 'energy_id', 'substrate_id', 'feature_id',
            'gear_id', 'a', 'x', 'y', 'z', 'znet', 'hours_fished', 'value',
        ]
        for r in results:
            rd = {}
            for field in fields:
                value = getattr(r, field)
                if isinstance(value, unicode):
                    value = str(value)
                rd[field] = value
            dicts.append(rd)
        return dicts

    def sort_result_dicts(self, result_dicts):
        sort_fields = [
            't', 'cell_id', 'energy_id', 'substrate_id', 'feature_id',
            'gear_id'
        ]

        for field in sort_fields:
            result_dicts.sort(key=lambda rd: rd[field])

if __name__ == '__main__' :
    unittest.main()

