import tempfile
import os
import csv
import fiona
import shapely.geometry
import shapely.wkb
import sasi_runner.util.gis as gis_util


def generate_data(data_dir="", time_start=0, time_end=10, time_step=1):
    if not data_dir:
        data_dir = tempfile.mkdtemp(prefix="tst.")

    sections = {}
    sections['substrates'] = {
        'id': 'substrates',
        'type': 'csv',
        'fields': ['id'],
        'data': [{'id': "S%s" % i} for i in range(5)]
    }

    sections['energies'] = {
        'id': 'energies',
        'type': 'csv',
        'fields': ['id'],
        'data': [{'id': "High"}, {'id': 'Low'}]
    }
        
    sections['features'] = {
        'id': 'features',
        'type': 'csv',
        'fields': ['id', 'category'],
        'data': [{'id': "F%s" % i, 'category': ('bio' if i % 2 else 'geo')}
                 for i in range(10) ]
    }

    sections['gears'] = {
        'id': 'gears',
        'type': 'csv',
        'fields': ['id'],
        'data': [{'id': "G%s" % i} for i in range(5)]
    }

    sections['model_parameters'] = {
        'id': 'model_parameters',
        'type': 'csv',
        'fields': ['time_start', 'time_end', 'time_step', 
                   't_0', 't_1', 't_2', 't_3', 
                   'w_0', 'w_1', 'w_2', 'w_3', 
                   'projection'],
        'data': [{'time_start': time_start, 'time_end': time_end, 'time_step':
                  time_step, 
                  't_0': 0, 't_1': 1, 't_2': 2, 't_3': 3, 
                  'w_0': 0, 'w_1': .1, 'w_2': .2, 'w_3':.3, 
                  'projection': None}]
    }


    va_data = []
    i = 0
    for s in sections['substrates']['data']:
        for e in sections['energies']['data']:
            for f in sections['features']['data']:
                for g in sections['gears']['data']:
                    va_data.append({
                        'Gear ID': g['id'],
                        'Feature ID': f['id'],
                        'Substrate ID': s['id'],
                        'Energy': e['id'],
                        'S': (i % 3) + 1,
                        'R': (i % 3) + 1,
                    })
                    i += 1
    sections['va'] = {
        'id': 'va',
        'type': 'csv',
        'fields': ['Gear ID', 'Feature ID', 'Substrate ID', 'Energy', 
                   'S', 'R'],
        'data': va_data
    }

    grid_size = 3

    hab_records = []
    i = 0
    for j in range(-2, grid_size + 2):
        for k in range(-2, grid_size + 2):
            x = j * 2
            y = k * 2
            substrate_data = sections['substrates']['data']
            substrate = substrate_data[i % len(substrate_data)]['id']
            energy_data = sections['energies']['data']
            energy = energy_data[i % len(energy_data)]['id']
            z = -1.0 * i
            coords = [[x,y], [x, y+2], [x+2, y+2], [x+2, y], [x,y]]
            hab_records.append({
                'id': i,
                'geometry': {
                    'type': 'MultiPolygon',
                    'coordinates': [[coords]]
                },
                'properties': {
                    'SUBSTRATE': substrate,
                    'ENERGY': energy,
                    'Z': z
                }
            })
            i += 1
    sections['habitats'] = {
        'id': 'habitats',
        'type': 'shp',
        'schema': {
            'geometry': 'MultiPolygon',
            'properties': {
                'SUBSTRATE': 'str',
                'ENERGY': 'str',
                'Z': 'float'
            }
        },
        'records': hab_records
    }

    cell_records = []
    i = 0
    for j in range(grid_size):
        for k in range(grid_size):
            x = (j * 2) + 1
            y = (k * 2) + 1
            coords = [[x,y], [x, y+2], [x+2, y+2], [x+2, y], [x,y]]
            cell_records.append({
                'id': i,
                'geometry': {
                    'type': 'MultiPolygon',
                    'coordinates': [[coords]]
                },
                'properties': {
                    'TYPE_ID': "%s" % i,
                    'TYPE': "km100"
                }
            })
            i += 1
    sections['grid'] = {
        'id': 'grid',
        'type': 'shp',
        'schema': {
            'geometry': 'MultiPolygon',
            'properties': {
                'TYPE': 'str',
                'TYPE_ID': 'str',
            }
        },
        'records': cell_records
    }

    fishing_efforts_data = []
    num_gears = len(sections['gears']['data'])
    for cell_record in sections['grid']['records']:
        cell_shape = shapely.geometry.shape(cell_record['geometry'])
        cell_area = gis_util.get_area(shapely.wkb.dumps(cell_shape))
        for t in range(time_start, time_end, time_step):
            for g in sections['gears']['data']:
                fishing_efforts_data.append({
                    'cell_id': cell_record['id'],
                    'time': t,
                    'swept_area': cell_area/num_gears,
                    'gear_id': g['id']
                })

    sections['fishing_efforts'] = {
        'id': 'fishing_efforts',
        'type': 'fishing_efforts',
        'model_type': 'realized',
        'fields': ['cell_id', 'time', 'swept_area', 'gear_id'],
        'data': fishing_efforts_data
    }

    for s in sections.values():
        if s['type'] == 'csv':
            generate_csv_section(data_dir, s)
        elif s['type'] == 'shp':
            generate_shp_section(data_dir, s)
        elif s['type'] == 'fishing_efforts':
            generate_fishing_efforts_section(data_dir, s)

    return data_dir

def setup_section_dirs(data_dir, section):
    section_dir = os.path.join(data_dir, section['id'])
    os.mkdir(section_dir)
    section_data_dir = os.path.join(section_dir, 'data')
    os.mkdir(section_data_dir)
    return section_data_dir

def generate_csv_section(data_dir, section):
    section_data_dir = setup_section_dirs(data_dir, section)
    w = csv.writer(
        open(os.path.join(section_data_dir, "%s.csv" % section['id']), "w"))
    w.writerow(section['fields'])
    for row in section['data']:
        w.writerow([row.get(field, '') for field in section['fields']])

def generate_shp_section(data_dir, section):
    section_data_dir = setup_section_dirs(data_dir, section)
    shpfile = os.path.join(section_data_dir, "%s.shp" % section['id'])
    c = fiona.collection(shpfile, "w", driver='ESRI Shapefile', 
                         crs={'no_defs': True, 'ellps': 'WGS84', 
                              'datum': 'WGS84', 'proj': 'longlat'},
                         schema=section['schema']
                        )
    for record in section['records']:
        c.write(record)
    c.close()

def generate_fishing_efforts_section(data_dir, section):
    generate_csv_section(data_dir, section)
    section_dir = os.path.join(data_dir, section['id'])
    w = csv.writer(open(os.path.join(section_dir, 'model.csv'),'w'))
    w.writerow(['model_type'])
    w.writerow([section['model_type']])
