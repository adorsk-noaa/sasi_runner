from sasi_runner.app import db
from sqlalchemy import Table, Column, Integer, String, DateTime
from sqlalchemy.orm import mapper
from datetime import datetime


class SASIFile(object):
    def __init__(self, id=None, path=None, filename=None, category=None,
                 size=None, created=None):
        self.id = id
        self.path = path
        self.filename = filename
        self.category = category
        self.size = size
        self.created = created

    def to_dict(self):
        file_dict = {}
        for attr in ['id', 'filename', 'category', 'size', 'created']:
            value = getattr(self, attr, None)
            if isinstance(value, datetime):
                value = value.isoformat()
            file_dict[attr] = value
        return file_dict

table = Table('sasi_file', db.metadata,
              Column('id', Integer, primary_key=True),
              Column('path', String),
              Column('filename', String),
              Column('category', String),
              Column('size', Integer),
              Column('created', DateTime),
             )

mapper(SASIFile, table)
