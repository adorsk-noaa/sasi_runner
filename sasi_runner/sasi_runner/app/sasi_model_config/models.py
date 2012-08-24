from sasi_runner.app import db 
from sasi_runner.app.sasi_file import models as sasi_file_models
from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import mapper, relationship

file_attrs = [
    'substrates',
    'features',
    'gears',
    'habitats',
    'grid',
    'va',
    'model_parameters',
    'map_layers',
    'fishing_efforts'
]
class SASIModelConfig(object):
    def __init__(self, id=None, title="New Configuration", **kwargs): 
        self.id = id
        for attr in file_attrs:
            setattr(self, attr, kwargs.get(attr))

file_columns = []
for attr in file_attrs:
    column = Column(attr + "_file", Integer,
                    ForeignKey(sasi_file_models.table.c.id))
    file_columns.append(column)

table = Table('sasi_model_config', db.metadata,
              Column('id', Integer, primary_key=True),
              Column('title', String),
              *file_columns
             )

relationships = {}
for attr in file_attrs:
    relationships[attr] = relationship(sasi_file_models.SASIFile, 
        primaryjoin=(table.c[attr + "_file"]==sasi_file_models.table.c.id))

mapper(SASIModelConfig, table, properties=relationships)
