from sasi_runner.app import db 
from sasi_runner.app.sasi_file import models as sasi_file_models
from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import mapper, relationship

class SASIResult(object):
    def __init__(self, id=None, title="", result_file=None): 
        self.id = id
        self.title = title
        self.result_file = result_file

    def to_dict(self):
        result_dict = {}
        for attr in ['id', 'title']:
            result_dict[attr] = getattr(self, attr, None)
        if self.result_file:
            file_id = self.result_file.id
        else:
            file_id = None
        result_dict['file_id'] = file_id
        return result_dict

table = Table('sasi_result', db.metadata,
              Column('id', Integer, primary_key=True),
              Column('title', String),
              Column("result_file_id", Integer,
                     ForeignKey(sasi_file_models.table.c.id))
             )

relationships = {
    'result_file': relationship(
        sasi_file_models.SASIFile, 
        primaryjoin=(table.c["result_file_id"]==sasi_file_models.table.c.id)
    )
}

mapper(SASIResult, table, properties=relationships)
