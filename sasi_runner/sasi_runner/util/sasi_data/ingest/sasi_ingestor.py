import sasi_runner.util.sasi_data.ingest as ingest_util
import sasi_runner.util.sasi_data.models as sasi_models
import sasi_runner.util.gis as gis_util
import os
import csv


class SASI_Ingestor(object):
    def __init__(self, dao=None):
        self.dao = dao

    def ingest(self, data_dir=None):
        csv_sections = [
            {
                'id': 'substrates',
                'class': sasi_models.Substrate,
                'mappings': [
                    {'source': 'id', 'target': 'id'}
                ]
            },
            {
                'id': 'features',
                'class': sasi_models.Feature,
                'mappings': [
                    {'source': 'id', 'target': 'id'},
                    {'source': 'category', 'target': 'category'}
                ]
            },
            {
                'id': 'gears',
                'class': sasi_models.Gear,
                'mappings': [
                    {'source': 'id', 'target': 'id'},
                ]
            },
            {
                'id': 'va',
                'class': sasi_models.VA,
                'mappings': [
                    {'source': 'Gear ID', 'target': 'gear_id'},
                    {'source': 'Feature ID', 'target': 'feature_id'},
                    {'source': 'Substrate ID', 'target': 'substrate_id'},
                    {'source': 'Energy', 'target': 'energy'},
                    {'source': 'S', 'target': 's'},
                    {'source': 'R', 'target': 'r'},
                ]
            },
            {
                'id': 'model_parameters',
                'class': sasi_models.ModelParameters,
                'mappings': [
                    {'source': 'time_start', 'target': 'time_start'},
                    {'source': 'time_end', 'target': 'time_end'},
                    {'source': 'time_step', 'target': 'time_step'},
                    {'source': 't_0', 'target': 't_0'},
                    {'source': 't_1', 'target': 't_1'},
                    {'source': 't_2', 'target': 't_2'},
                    {'source': 't_3', 'target': 't_3'},
                    {'source': 'w_0', 'target': 'w_0'},
                    {'source': 'w_1', 'target': 'w_1'},
                    {'source': 'w_2', 'target': 'w_2'},
                    {'source': 'w_3', 'target': 'w_3'},
                    {'source': 'projection', 'target': 'projection',
                     # Use the mollweide projection as the default.
                     'default': ("+proj=moll +lon_0=0 +x_0=0 +y_0=0 "
                                 "+ellps=WGS84 +datum=WGS84 +units=m "
                                 "+no_defs")
                    }
                ],
            }
        ]

        for section in csv_sections:
            csv_file = os.path.join(data_dir, section['id'], 'data',
                                    "%s.csv" % section['id'])
            ingestor = ingest_util.CSV_Ingestor(dao=self.dao, 
                csv_file=csv_file, clazz=section['class'],
                mappings=section['mappings'],) 
            ingestor.ingest()

        # Keep a shortcut to the model parameters.
        self.model_parameters = self.dao.query('{{ModelParameters}}').fetchone()

        # Shapefile data.
        shp_sections = [
            {
                'id': 'habitats',
                'class': sasi_models.Habitat,
                'mappings': [
                    {'source': 'SUBSTRATE', 'target': 'substrate'},
                    {'source': 'ENERGY', 'target': 'energy'},
                    {'source': 'Z', 'target': 'z', 
                     'processor': lambda value: -1.0 * float(value)},
                ]
            },
            {
                'id': 'grid',
                'class': sasi_models.Cell,
                'mappings': [
                    {'source': 'TYPE', 'target': 'type'},
                    {'source': 'TYPE_ID', 'target': 'type_id'},
                ]
            }
        ]
        for section in shp_sections:
            shp_file = os.path.join(data_dir, section['id'], 'data',
                                    "%s.shp" % section['id'])
            ingestor = ingest_util.Shapefile_Ingestor(dao=self.dao,
                shp_file=shp_file, clazz=section['class'], 
                mappings=section['mappings'] ) 
            ingestor.ingest()

        # Fishing efforts.
        effort_dir = os.path.join(data_dir, 'fishing_efforts')
        effort_model_file = os.path.join(effort_dir, 'model.csv')
        model_info_reader = csv.DictReader(open(effort_model_file, 'rb'))
        model_info = model_info_reader.next()
        self.effort_model_type = model_info.get('model_type')
        if self.effort_model_type == 'realized':
            csv_file = os.path.join(effort_dir, 'data', 'fishing_efforts.csv')
            mappings = []
            for attr in ['cell_id', 'time', 'swept_area', 'gear_id']:
                mappings.append({ 'source': attr, 'target': attr, })
            ingestor = ingest_util.CSV_Ingestor(dao=self.dao, csv_file=csv_file,
                                    clazz=sasi_models.Effort,
                                    mappings=mappings
                                   )
            ingestor.ingest()

        self.post_ingest()

    def post_ingest(self):
        self.calculate_habitat_areas()
        self.calculate_cell_compositions()
        # @TODO: Setup fishing efforts here.

    def calculate_habitat_areas(self):
        for habitat in self.dao.query('{{Habitat}}'):
            habitat.area = gis_util.get_area(
                str(habitat.geom.geom_wkb), 
                target_proj=str(self.model_parameters.projection)
            )
            self.dao.save(habitat, auto_commit=False)
        self.dao.commit()

    def calculate_cell_compositions(self):
        for cell in self.dao.query('{{Cell}}'):
            composition = {}
            cell.z = 0

            # Calculate cell area.
            cell.area = gis_util.get_area(
                str(cell.geom.geom_wkb),
                target_proj=str(self.model_parameters.projection)
            )

            # Calculate habitat composition.
            intersecting_habitats = self.dao.query({
                'SELECT': '{{Habitat}}',
                'WHERE':  [
                    [{'TYPE': 'ENTITY', 
                      'EXPRESSION': ('func.st_intersects({{Habitat.geom}},'
                                     '{{Cell.geom}})')
                     }, '==', True],
                    [{'TYPE': 'ENTITY', 'EXPRESSION': '{{Cell.id}}'}, 
                     '==', cell.id]
                ]
            })

            for habitat in intersecting_habitats:
                intersection = gis_util.get_intersection(
                    str(habitat.geom.geom_wkb),
                    str(cell.geom.geom_wkb),
                )
                intersection_area = gis_util.get_area(
                    str(intersection),
                    target_proj=str(self.model_parameters.projection)
                )
                hab_key = (habitat.substrate, habitat.energy,)
                pct_area = intersection_area/cell.area
                composition[hab_key] = composition.get(hab_key, 0) + pct_area
                cell.z += pct_area * habitat.z
            cell.habitat_composition = composition

            self.dao.save(cell, auto_commit=False)
        self.dao.commit()
