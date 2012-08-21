from sasi_runner.app import db 
from sqlalchemy import Table, Column, Integer
from sqlalchemy.orm import mapper


class SASIModelConfig(object):
    def __init__(self, id=None):
        self.id = id

table = Table('sasi_model_config', db.metadata,
              Column('id', Integer, primary_key=True),
             )

mapper(SASIModelConfig, table)
