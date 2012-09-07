import sasi_data.exporters as exporters
import sasi_data.processors as processors
from jinja2 import Environment, PackageLoader
import os



class GeoRefinePackager(object):

    def __init__(self, package_dir="", cells=[], energys=[],
                 substrates=[], features=[], gears=[], results=[],
                 map_parameters=None): 
        self.package_dir = package_dir
        self.cells = cells
        self.energys = energys
        self.substrates = substrates
        self.features = features
        self.gears = gears
        self.results = results
        self.map_parameters = map_parameters
        self.template_env = Environment(
            loader=PackageLoader(
                'sasi_runner.app.sasi_model_config.util.packagers', 
                'templates'
            ),
            variable_start_string='{=',
            variable_end_string='=}'
        )

    def create_package(self):
        self.create_package_dirs()
        self.create_data_files()
        self.create_schema_files()
        self.create_app_config_files()
        pass

    def create_package_dirs(self):
        self.data_dir = os.path.join(self.package_dir, "data")
        os.mkdir(self.data_dir)

    def create_data_files(self):
        # Define mappings, section by section.
        sections = [
            {
                'id': 'cells',
                'data': self.cells,
                'mappings': [
                    'id',
                    'type',
                    'type_id',
                    'area',
                    {'source': 'geom', 'target': 'geom', 
                     'processor': processors.sa_wkb_to_wkt
                    }
                ]
            },

            {
                'id': 'energys',
                'data': self.energys,
                'mappings': [
                    'id',
                    'label',
                    'description',
                ]
            },

            {
                'id': 'substrates',
                'data': self.substrates,
                'mappings': [
                    'id',
                    'label',
                    'description',
                ]
            },

            {
                'id': 'features',
                'data': self.features,
                'mappings': [
                    'id',
                    'label',
                    'category',
                    'description',
                ]
            },

            {
                'id': 'gears',
                'data': self.gears,
                'mappings': [
                    'id',
                    'label',
                    'description',
                ]
            },

            {
                'id': 'results',
                'data': self.results,
                'mappings': [
                    'id',
                    't',
                    'cell_id',
                    'gear_id',
                    'substrate_id',
                    'energy_id',
                    'feature_id',
                    'a',
                    'x',
                    'y',
                    'z',
                    'znet'
                ]
            }
        ]

        for section in sections:
            csv_file = os.path.join(self.data_dir, "%s.csv" % section['id'])
            exporters.CSV_Exporter(
                csv_file=csv_file,
                objects=section['data'],
                mappings=section['mappings']
            ).export()

    def create_schema_files(self):
        schema_file = os.path.join(self.package_dir, "schema.py")
        schema_fh = open(schema_file, "w")
        schema_template = self.template_env.get_template(
            os.path.join('georefine', 'schema.py'))
        schema_fh.write(schema_template.render())
        schema_fh.close()

    def create_app_config_files(self):
        app_config_file = os.path.join(self.package_dir, "app_config.py")
        app_config_fh = open(app_config_file, "w")
        app_config_template = self.template_env.get_template(
            os.path.join('georefine', 'app_config.py'))
        app_config_fh.write(app_config_template.render(
            map_parameters=self.map_parameters))
        app_config_fh.close()
