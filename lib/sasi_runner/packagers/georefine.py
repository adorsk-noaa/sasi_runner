import sasi_data.exporters as exporters
from sasi_data.util import shapefile as shapefile_util
from sasi_data.util import gis as gis_util
from jinja2 import Environment, PackageLoader
import os
import zipfile
import csv
import json
import shutil
import tempfile
import logging


class LoggerLogHandler(logging.Handler):
    """ Custom log handler that logs messages to another
    logger. This can be used to chain together loggers. """
    def __init__(self, logger=None, **kwargs):
        logging.Handler.__init__(self, **kwargs)
        self.logger = logger

    def emit(self, record):
        self.logger.log(record.levelno, self.format(record))

class GeoRefinePackager(object):

    def __init__(self, data, model_parameters={}, source_dir=None, 
                 metadata_dir=None, logger=logging.getLogger(), 
                 output_file=None): 
        self.data = data
        self.model_parameters = model_parameters
        self.source_dir = source_dir
        self.metadata_dir = metadata_dir
        self.logger = logger
        self.target_dir = tempfile.mkdtemp(prefix="grp.")

        self.static_dir = os.path.join(self.target_dir, 'static')
        os.makedirs(self.static_dir)

        self.layers_dir = os.path.join(self.static_dir, 'map_layers')
        os.makedirs(self.layers_dir)
        
        if not output_file:
            os_hndl, output_file = tempfile.mkstemp(suffix=".georefine.zip")
        self.output_file = output_file

        self.template_env = Environment(
            loader=PackageLoader('sasi_runner.packagers', 'templates'),
            variable_start_string='{=',
            variable_end_string='=}',
        )

    def create_package(self):
        self.create_target_dirs()
        self.create_data_files()
        self.create_schema_files()
        self.create_static_files()
        archive_file = self.create_archive(self.output_file)
        #shutil.rmtree(self.target_dir)
        return archive_file

    def create_target_dirs(self):
        self.data_dir = os.path.join(self.target_dir, "data")
        os.mkdir(self.data_dir)

    def create_data_files(self):
        # Define mappings, section by section.
        sections = [
            {
                'id': 'time',
                'data': self.data['time'],
                'mappings': [
                    'id',
                ]
            },

            {
                'id': 'cell',
                'data': self.data['cell'],
                'mappings': [
                    'id',
                    'type',
                    'type_id',
                    'area',
                    'depth',
                    'geom_wkt'
                ]
            },

            {
                'id': 'energy',
                'data': self.data['energy'],
                'mappings': [
                    'id',
                    'label',
                    'description',
                ]
            },

            {
                'id': 'substrate',
                'data': self.data['substrate'],
                'mappings': [
                    'id',
                    'label',
                    'description',
                ]
            },

            {
                'id': 'feature',
                'data': self.data['feature'],
                'mappings': [
                    'id',
                    'label',
                    'category',
                    'description',
                ]
            },

            {
                'id': 'feature_category',
                'data': self.data['feature_category'],
                'mappings': [
                    'id',
                    'label',
                    'description',
                ]
            },

            {
                'id': 'gear',
                'data': self.data['gear'],
                'mappings': [
                    'id',
                    'generic_id',
                    'is_generic',
                    'label',
                    'description',
                    'min_depth',
                    'max_depth',
                ]
            },

            {
                'id': 'sasi_result',
                'data': self.data['sasi_result'],
                'mappings': [
                    'id',
                    't',
                    'cell_id',
                    'gear_id',
                    'substrate_id',
                    'energy_id',
                    'feature_id',
                    'feature_category_id',
                    'a',
                    'x',
                    'y',
                    'z',
                    'znet',
                ]
            },

            {
                'id': 'fishing_result',
                'data': self.data['fishing_result'],
                'mappings': [
                    'id',
                    't',
                    'cell_id',
                    'gear_id',
                    'generic_gear_id',
                    'a',
                    'value',
                    'value_net',
                    'hours_fished',
                    'hours_fished_net'
                ]
            }
        ]

        for section in sections:
            csv_file = os.path.join(self.data_dir, "%s.csv" % section['id'])

            base_msg = "Exporting '%s'..." % section['id']
            self.logger.info(base_msg)
            section_logger = self.get_logger_for_section(
                section['id'], base_msg)

            exporters.CSV_Exporter(
                csv_file=csv_file,
                data=section['data'],
                mappings=section['mappings'],
                logger=section_logger,
            ).export()

    def create_schema_files(self):
        schema_file = os.path.join(self.target_dir, "schema.py")
        with open(schema_file, "wb") as f:
            schema_template = self.template_env.get_template(
                'georefine/schema.py')
            f.write(schema_template.render())

    def create_static_files(self):

        # Create substrates layer.
        self.create_substrates_layer()

        # Copy layer dirs.
        layers_source_dir = os.path.join(self.source_dir, 'map_layers')
        if os.path.isdir(layers_source_dir):
            for layer_id in os.listdir(layers_source_dir):  
                layer_source_dir = os.path.join(layers_source_dir, layer_id)
                if os.path.isdir(layer_source_dir):
                    layer_target_dir = os.path.join(self.layers_dir, layer_id)
                    shutil.copytree(
                        layer_source_dir,
                        layer_target_dir
                    )

        # Get layer data from target dir.
        layers = []
        for layer_id in os.listdir(self.layers_dir):  
            layer_dir = os.path.join(self.layers_dir, layer_id)
            if os.path.isdir(layer_source_dir):
                layer = {
                    'id': layer_id,
                    'dir': layer_dir,
                }
                config_path = os.path.join(layer_dir, 'client.json')
                if os.path.isfile(config_path):
                    with open(config_path, 'rb') as f:
                        layer['json_config'] = f.read()
                layers.append(layer)

        # Create GeoRefine appConfig.
        map_config = self.read_map_config()
        app_config_file = os.path.join(self.static_dir, "GeoRefine_appConfig.js")
        with open(app_config_file, "wb") as f:
            app_config_template = self.template_env.get_template(
                'georefine/GeoRefine_appConfig.js')
            f.write(app_config_template.render(
                model_parameters=self.model_parameters,
                map_config=map_config,
                layers=layers,
            ))

        # Copy metadata.
        if os.path.isdir(self.metadata_dir):
            shutil.copytree(
                self.metadata_dir, 
                os.path.join(self.static_dir, 'sasipedia')
            )

        # Set permissions.
        for root, dirs, files in os.walk(self.static_dir):  
            for item in dirs + files:  
                os.chmod(os.path.join(root, item), 0755)

    def read_map_config(self):
        map_config_path = os.path.join(self.data_dir, "map_config.json")
        if os.path.isfile(map_config_path):
            with open(map_config_file, "rb") as f:
                return json.load(f)
        return {}

    def create_archive(self, output_file):
        def zipdir(basedir, archivename, basename=None):
            z = zipfile.ZipFile(archivename, "w", zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(basedir):
                for fn in files:
                    absfn = os.path.join(root, fn)
                    zf_path_parts = [absfn[len(basedir)+len(os.sep):]]
                    if basename:
                        zf_path_parts.insert(0, basename)
                    zfn = os.path.join(*zf_path_parts)
                    z.write(absfn, zfn)
            z.close()
        zipdir(self.target_dir, output_file)
        return output_file

    def get_logger_for_section(self, section_id=None, base_msg=None):
        logger = logging.getLogger("%s_%s" % (id(self), section_id))
        formatter = logging.Formatter(base_msg + ' %(message)s.')
        log_handler = LoggerLogHandler(self.logger)
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)
        logger.setLevel(self.logger.level)
        return logger

    def create_substrates_layer(self):
        logger = self.get_logger_for_section(
            section_id='substrates_layer', 
            base_msg="Creating substrates layer...")
        # Read substrates.
        substrates = []
        substrates_path = os.path.join(
            self.source_dir, 'substrates.csv')
        with open(substrates_path, 'rb') as f:
            for row in csv.DictReader(f):
                css_color = row.get('color', '#000000')
                hex_color = css_color.lstrip('#')
                row['rgb'] = [int(hex_color[i:i+2],16) for i in range(0, 6, 2)]
                substrates.append(row)

        # Make substrate shapefile from habitats, 
        # with EPSG:3857 as the CRS.
        layer_dir = os.path.join(self.layers_dir, 'substrates')
        os.makedirs(layer_dir)
        habs_shapefile = os.path.join(
            self.source_dir, 'habitats', 'habitats.shp')
        logger.info("Reading shapes from habitats file...")
        reader = shapefile_util.get_shapefile_reader(habs_shapefile)
        source_mbr = reader.get_mbr()
        source_crs = reader.get_crs()
        source_schema = reader.get_schema()
        
        write_msg = "Writing out data for substrates layer..."
        logger.info(write_msg)
        reader = shapefile_util.get_shapefile_reader(habs_shapefile)
        substrate_shapefile = os.path.join(layer_dir, 'substrates.shp')
        writer = shapefile_util.get_shapefile_writer(
            shapefile=substrate_shapefile, 
            crs='EPSG:3857',
            schema=source_schema,
        )
        skipped = 0
        counter = 0
        log_interval = 1e3
        for record in reader.records():
            counter += 1
            if (counter % log_interval) == 0:
                prog_msg = "%s %d of %d (%.1f)" % (
                    write_msg, counter, reader.size, 
                    100.0 * counter/reader.size)
                logger.info(prog_msg)
            shp = gis_util.geojson_to_shape(record['geometry'])
            proj_shp = gis_util.reproject_shape(shp, source_crs, 'EPSG:3857')
            record['geometry'] = json.loads(gis_util.shape_to_geojson(proj_shp))
            bad_rec = False
            ps = record['properties']
            if type(ps['ENERGY']) is not unicode:
                bad_rec = True
            if type(ps['Z']) is not float:
                bad_rec = True
            if type(ps['SUBSTRATE']) is not unicode:
                bad_rec = True
            if record['geometry']['type'] != 'Polygon':
                bad_rec = True

            if not bad_rec:
                writer.write(record)
            else:
                skipped += 1

        writer.close()
        reader.close()
        if skipped:
            self.logger.info("%s Skipped %s records due to formatting" %
                             (write_msg, skipped))

        # Transform bounds to EPSG:3857.
        mbr_diag = gis_util.wkt_to_shape(
            "LINESTRING (%s %s, %s %s)" % source_mbr)
        projected_diag = gis_util.reproject_shape(
            mbr_diag, source_crs, 'EPSG:3857')
        projected_mbr = gis_util.get_shape_mbr(projected_diag)

        # Write layer client config.
        client_path = os.path.join(layer_dir, 'client.json')
        info_template = self.template_env.get_template(
            'georefine/substrates_info.html')
        info_html = info_template.render(substrates=substrates)
        client_config = {
            'id': 'substrates',
            'label': 'Substrates',
            'source': 'georefine_wms',
            'layer_type': "WMS",
            'params': {
                'srs':'EPSG:3857',
                'transparent': True,
                'layers': 'substrates',
            },
            'info': info_html,
            'properties': {
                'maxExtent': projected_mbr,
                'projection': 'EPSG:3857',
                'serverResolutions': [4891.96981024998, 2445.98490512499, 1222.99245256249, 611.49622628138, 305.748113140558],
                'tileSize': {'w': 512, 'h': 512},
                'visibility': False
            },
            'zIndex': 30,
        }
        with open(client_path, 'wb') as f:
            json.dump(client_config, f)

        # Write mapfile.
        mapfile_path = os.path.join(layer_dir, 'substrates.map')
        with open(mapfile_path, 'wb') as f:
            mapfile_template = self.template_env.get_template(
                'georefine/substrates.map')
            f.write(mapfile_template.render(
                substrates=substrates,
                mbr=projected_mbr
            ))

        # Write wms config.
        wms_config_path = os.path.join(layer_dir, 'wms.json')
        wms_config = {
            'mapfile': 'substrates.map'
        }
        with open(wms_config_path, 'wb') as f:
            json.dump(wms_config, f)
