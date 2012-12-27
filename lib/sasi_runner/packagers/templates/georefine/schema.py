from sqlalchemy import (Table, Column, ForeignKey, ForeignKeyConstraint, 
                        Integer, String, Float, Index)
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
        Column('z', Float),
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
        Column('label', String),
        )
ordered_sources.append({'id': 'gear', 'source': sources['gear']})

sources['result']= Table('result', metadata,
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
        Column('hours_fished', Float),
        Column('value', Float),
        )
# Create time/field/cell indices. These are essential for filtering in a reasonable
# amount of time.
for col in ['energy_id', 'cell_id', 'gear_id', 'substrate_id',
            'feature_category_id', 'feature_id']:
    Index('idx_t_%s_cell_id' % col, sources['result'].c.t, sources['result'].c[col],
          sources['result'].c.cell_id)
ordered_sources.append({'id': 'result', 'source': sources['result']})

# This dictionary contains the schema objects GeoRefine will use.
schema = {
    'sources': sources,
    'ordered_sources': ordered_sources,
    'metadata': metadata,
}
