import unittest
from sasi_runner.packagers import GeoRefinePackager
import sasi_data.util.data_generators as data_generators
import sasi_data.models as models
import csv
import tempfile
import os
import shutil


class GeoRefinePackagerTest(unittest.TestCase):

    def tearDown(self):
        if hasattr(self, 'target_dir') and self.target_dir:
            pass
            #shutil.rmtree(self.target_dir)

    def test_georefine_packager(self):
        cells = data_generators.generate_cell_grid()
        energys = data_generators.generate_energys()
        features = data_generators.generate_features()
        substrates = data_generators.generate_substrates()
        gears = data_generators.generate_gears()
        #results = data_generators.generate_results(
            #times=range(0,3), cells=cells, energys=energys,
            #features=features, substrates=substrates, gears=gears)

        # Directory for GeoRefine-specific data files.
        source_dir = data_generators.generate_data_dir()

        metadata_dir = tempfile.mkdtemp(prefix="gr_md.")
        open(os.path.join(metadata_dir, "foo.html"), "wb").write("Hi")

        packager = GeoRefinePackager(
            data={
                'time': [t for t in range(0,10)],
                'cell': cells,
                'energy': energys,
                'substrate': substrates,
                'feature': features,
                'feature_category': [],
                'gear': gears,
                'sasi_result': [],
                'fishing_result': [],
            },
            source_dir=source_dir,
            metadata_dir=metadata_dir
        )

        archive_file = packager.create_package()
        self.target_dir = packager.target_dir
        print self.target_dir
        print archive_file

if __name__ == '__main__':
    unittest.main()
