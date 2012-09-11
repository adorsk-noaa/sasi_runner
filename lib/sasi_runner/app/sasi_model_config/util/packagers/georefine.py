import sasi_data.exporters as exporters
import sasi_data.processors as processors
from jinja2 import Environment, PackageLoader
import os
import csv
import shutil


class GeoRefinePackager(object):

    def __init__(self, target_dir="", cells=[], energys=[],
                 substrates=[], features=[], gears=[], results=[],
                 source_data_dir=""): 
        self.target_dir = target_dir
        self.cells = cells
        self.energys = energys
        self.substrates = substrates
        self.features = features
        self.gears = gears
        self.results = results
        self.source_data_dir = source_data_dir

        self.template_env = Environment(
            loader=PackageLoader(
                'sasi_runner.app.sasi_model_config.util.packagers', 
                'templates'
            ),
            variable_start_string='{=',
            variable_end_string='=}'
        )

    def create_package(self):
        self.create_target_dirs()
        self.create_data_files()
        self.copy_map_layers()
        self.create_schema_files()
        self.create_app_config_files()
        pass

    def create_target_dirs(self):
        self.data_dir = os.path.join(self.target_dir, "data")
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

    def copy_map_layers(self):
        target_dir = os.path.join(self.data_dir, "map_layers")
        source_dir = os.path.join(self.source_data_dir, 'map_layers')
        if os.path.isdir(source_dir):
            shutil.copytree(source_dir, target_dir)

    def create_schema_files(self):
        schema_file = os.path.join(self.target_dir, "schema.py")
        schema_fh = open(schema_file, "w")
        schema_template = self.template_env.get_template(
            os.path.join('georefine', 'schema.py'))
        schema_fh.write(schema_template.render())
        schema_fh.close()

    def create_app_config_files(self):
        map_parameters = self.get_map_parameters()

        map_layers = self.get_map_layers()
        formatted_map_layers = self.format_layers_for_app_config(map_layers)

        app_config_file = os.path.join(self.target_dir, "app_config.py")
        app_config_fh = open(app_config_file, "w")
        app_config_template = self.template_env.get_template(
            os.path.join('georefine', 'app_config.py'))
        app_config_fh.write(
            app_config_template.render(
                map_parameters=map_parameters,
                map_layers=formatted_map_layers
            )
        )
        app_config_fh.close()

    def get_map_parameters(self):
        map_parameters_file = os.path.join(
            self.source_data_dir, "map_parameters", "data", "map_parameters.csv")
        reader = csv.DictReader(open(map_parameters_file, "rb"))
        return reader.next()

    def get_map_layers(self):
        map_layers = {'base': [], 'overlay': []}
        map_layers_file = os.path.join(
            self.source_data_dir, "map_layers", "data", "map_layers.csv")
        reader = csv.DictReader(open(map_layers_file, "rb"))
        return [row for row in reader]

    def format_layers_for_app_config(self, layers):
        formatted_layers = {}
        for layer in layers:
            category = formatted_layers.setdefault(
                layer['layer_category'], [])
            formatted_layer = self.format_layer_for_app_config(layer)
            category.append(formatted_layer)
        return formatted_layers

    def format_layer_for_app_config(self, layer):
        """ Format a layer for use in an app config template. """
        formatted_layer = {'attrs': {}, 'wms_params': {}, 'options': {}}

        # Required directly mapped attributes.
        for attr in ['id', 'label', 'source', 'layer_type']:
            formatted_layer['attrs'][attr] = "'%s'" % layer[attr]

        # Optional directly mapped attributes.
        for attr in ['max_extent']:
            if not layer.get(attr) == None:
                formatted_layer['attrs'][attr] = "'%s'" % layer[attr]

        # Boolean attributes.
        for attr in ['disabled']:
            if layer.get(attr) == None:
                formatted_layer['attrs'][attr] = 'False'
            else:
                formatted_layer['attrs'][attr] = 'True'

        # Optional WMS Parameters.
        wms_params = {}
        for attr in ['layers', 'styles']:
            if layer.get(attr):
                wms_params[attr] = "'%s'" % layer[attr]
        for attr in ['transparent']:
            if not layer.get(attr) == None:
                wms_params[attr] = True
        formatted_layer['wms_params'] = wms_params

        return formatted_layer
