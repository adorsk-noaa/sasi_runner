from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, Integer, String, Float
from sqlalchemy.orm import relationship, mapper
from sqlalchemy import MetaData
from geoalchemy import *


sources = {}
ordered_sources = []
metadata = MetaData()

sources['cells'] = Table('cells', metadata,
        Column('id', Integer, primary_key=True),
        Column('z', Float),
        Column('area', Float),
        GeometryExtensionColumn('geom', MultiPolygon(2)),
        )
GeometryDDL(sources['cells'])
ordered_sources.append(sources['cells'])

sources['energys'] = Table('energys', metadata,
        Column('id', String, primary_key=True),
        Column('label', String),
        )
ordered_sources.append(sources['energys'])

sources['substrates'] = Table('substrates', metadata,
        Column('id', String, primary_key=True),
        Column('label', String),
        )
ordered_sources.append(sources['substrates'])

sources['features'] = Table('features', metadata,
        Column('id', String, primary_key=True),
        Column('label', String),
        Column('category', String),
        )
ordered_sources.append(sources['features'])

sources['gears'] = Table('gears', metadata,
        Column('id', String, primary_key=True),
        Column('label', String),
        )
ordered_sources.append(sources['gears'])

sources['results']= Table('results', metadata,
        Column('id', Integer, primary_key=True),
        Column('t', Integer),
        Column('energy_id', Integer, ForeignKey('energys.id')),
        Column('cell_id', Integer, ForeignKey('cells.id')),
        Column('gear_id', String, ForeignKey('gears.id')),
        Column('substrate_id', String, ForeignKey('substrates.id')),
        Column('feature_id', String, ForeignKey('features.id')),
        Column('a', Float),
        Column('x', Float),
        Column('y', Float),
        Column('z', Float),
        Column('znet', Float),
        )
ordered_sources.append(sources['results'])
