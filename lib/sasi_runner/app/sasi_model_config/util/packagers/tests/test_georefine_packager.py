import unittest
from sasi_runner.app.sasi_model_config.util.packagers import GeoRefinePackager
import sasi_data.util.data_generators as data_generators
import sasi_data.models as models
import tempfile
import os
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
        map_parameters = models.MapParameters(
            max_extent='[-70, 40, -60, 50]',
            graticule_intervals='[2]',
            resolutions='[0.025, 0.0125, 0.00625, 0.003125, 0.0015625, 0.00078125]'
        )
        map_layers_dir = tempfile.mkdtemp()
        for i in range(3):
            layer_id = "layer%s" % i
            layer_dir = os.path.join(map_layers_dir, layer_id)
            os.mkdir(layer_dir)
            data_generators.generate_map_layer(layer_id=layer_id,
                                               layer_dir=layer_dir)

        packager = GeoRefinePackager(
            package_dir=self.package_dir,
            cells=cells,
            energys=energys,
            substrates=substrates,
            features=features,
            gears=gears,
            results=results,
            map_parameters=map_parameters,
            map_layers_dir=map_layers_dir
        )

        packager.create_package()
        print self.package_dir

if __name__ == '__main__':
    unittest.main()
