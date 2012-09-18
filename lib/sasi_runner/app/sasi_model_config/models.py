from sasi_runner.app import db 
from sasi_runner.app.sasi_file import models as sasi_file_models
from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import mapper, relationship

file_attrs = [
    'substrates',
    'energys',
    'features',
    'gears',
    'habitats',
    'grid',
    'va',
    'model_parameters',
    'fishing_efforts',
    'georefine'
]
class SASIModelConfig(object):
    def __init__(self, id=None, title="New Configuration", bundle=None, **kwargs): 
        self.id = id
        self.title = title
        self.bundle = None
        for attr in file_attrs:
            setattr(self, attr, kwargs.get(attr))

    def clone(self):
        """
        Clone a config, w/out cloning its id.
        """
        clone = SASIModelConfig()
        for attr in file_attrs + ['title', 'bundle']:
            setattr(clone, attr, getattr(self, attr))
        return clone


file_columns = []
for attr in file_attrs + ['bundle']:
    column = Column(attr + "_file", Integer,
                    ForeignKey(sasi_file_models.table.c.id))
    file_columns.append(column)

table = Table('sasi_model_config', db.metadata,
              Column('id', Integer, primary_key=True),
              Column('title', String),
              *file_columns
             )

relationships = {}
for attr in file_attrs + ['bundle']:
    relationships[attr] = relationship(sasi_file_models.SASIFile, 
        primaryjoin=(table.c[attr + "_file"]==sasi_file_models.table.c.id))

mapper(SASIModelConfig, table, properties=relationships)
