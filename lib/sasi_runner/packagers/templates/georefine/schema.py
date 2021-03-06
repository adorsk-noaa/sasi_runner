from sqlalchemy import (Table, Column, ForeignKey, ForeignKeyConstraint, 
                        Integer, String, Boolean, Float, Index)
from sqlalchemy.orm import relationship, mapper
from sqlalchemy import MetaData
from geoalchemy import *

sources = {}
ordered_sources = []
metadata = MetaData()

# Times go in their own table to speed up time queries.
# Otherwise we have to scan all results to just get a list of times.
sources['time'] = Table('time', metadata,
        Column('id', Integer, primary_key=True),
        )
ordered_sources.append({'id': 'time', 'source': sources['time']})

sources['cell'] = Table('cell', metadata,
        Column('id', Integer, primary_key=True),
        Column('depth', Float),
        Column('area', Float),
        GeometryExtensionColumn('geom', MultiPolygon(2)),
        )
GeometryDDL(sources['cell'])
ordered_sources.append({'id': 'cell', 'source': sources['cell']})

sources['energy'] = Table('energy', metadata,
        Column('id', String, primary_key=True),
        Column('label', String),
        )
ordered_sources.append({'id': 'energy', 'source': sources['energy']})

sources['substrate'] = Table('substrate', metadata,
        Column('id', String, primary_key=True),
        Column('label', String),
        )
ordered_sources.append({'id': 'substrate', 'source': sources['substrate']})

sources['feature_category'] = Table('feature_category', metadata,
        Column('id', String, primary_key=True),
        Column('label', String),
        )
ordered_sources.append({'id': 'feature_category', 
                        'source': sources['feature_category']})

sources['feature'] = Table('feature', metadata,
        Column('id', String, primary_key=True),
        Column('label', String),
        Column('feature_category_id', String, ForeignKey('feature_category.id')),
        )
ordered_sources.append({'id': 'feature', 'source': sources['feature']})

sources['gear'] = Table('gear', metadata,
        Column('id', String, primary_key=True),
        Column('generic_id', String),
        Column('is_generic', Boolean),
        Column('min_depth', Float),
        Column('max_depth', Float),
        Column('label', String),
        )
ordered_sources.append({'id': 'gear', 'source': sources['gear']})

sources['sasi_result']= Table('sasi_result', metadata,
        Column('id', Integer, primary_key=True),
        Column('t', Integer),
        Column('energy_id', String, ForeignKey('energy.id')),
        Column('cell_id', Integer, ForeignKey('cell.id')),
        Column('gear_id', String, ForeignKey('gear.id')),
        Column('substrate_id', String, ForeignKey('substrate.id')),
        Column('feature_id', String, ForeignKey('feature.id')),
        Column('feature_category_id', String, ForeignKey('feature_category.id')),
        Column('a', Float),
        Column('x', Float),
        Column('y', Float),
        Column('z', Float),
        Column('znet', Float),
        )

# Create time/field/cell indices. These are essential for filtering in a reasonable
# amount of time.
for col in ['energy_id', 'gear_id', 'substrate_id',
            'feature_category_id', 'feature_id']:
    Index('idx_sasi_result_t_%s_cell_id' % col, sources['sasi_result'].c.t,
          sources['sasi_result'].c[col],
          sources['sasi_result'].c.cell_id)
ordered_sources.append({'id': 'sasi_result', 'source': sources['sasi_result']})

sources['fishing_result']= Table('fishing_result', metadata,
        Column('id', Integer, primary_key=True),
        Column('t', Integer),
        Column('cell_id', Integer, ForeignKey('cell.id')),
        Column('gear_id', String, ForeignKey('gear.id')),
        Column('generic_gear_id', String, ForeignKey('gear.id')),
        Column('a', Float),
        Column('hours_fished', Float),
        Column('hours_fished_net', Float),
        Column('value', Float),
        Column('value_net', Float),
        )
for col in ['gear_id', 'generic_gear_id']:
    Index('idx_fishing_result_t_%s_cell_id' % col,
          sources['fishing_result'].c.t, sources['fishing_result'].c[col],
          sources['fishing_result'].c.cell_id)
ordered_sources.append({'id': 'fishing_result', 
                        'source': sources['fishing_result']})

# This dictionary contains the schema objects GeoRefine will use.
schema = {
    'sources': sources,
    'ordered_sources': ordered_sources,
    'metadata': metadata,
}
