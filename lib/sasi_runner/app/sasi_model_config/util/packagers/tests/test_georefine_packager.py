import unittest
from sasi_runner.app.sasi_model_config.util.packagers import GeoRefinePackager
import sasi_data.util.data_generators as data_generators
import tempfile
import shutil


class GeoRefinePackagerTest(unittest.TestCase):
    def setUp(self):
        self.package_dir = tempfile.mkdtemp(prefix="grTest.")

    def tearDown(self):
        #shutil.rmtree(self.package_dir)
        pass

    def test_georefine_packager(self):
        cells = data_generators.generate_cell_grid()
        energys = data_generators.generate_energies()
        features = data_generators.generate_features()
        substrates = data_generators.generate_substrates()
        gears = data_generators.generate_gears()
        results = data_generators.generate_results(
            times=range(0,3), cells=cells, energies=energys,
            features=features, substrates=substrates, gears=gears)

        packager = GeoRefinePackager(
            package_dir=self.package_dir,
            cells=cells,
            energys=energys,
            substrates=substrates,
            features=features,
            gears=gears,
            results=results
        )

        packager.create_package()
        print self.package_dir

if __name__ == '__main__':
    unittest.main()
