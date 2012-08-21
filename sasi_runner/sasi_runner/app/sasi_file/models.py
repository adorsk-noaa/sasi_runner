from sasi_runner.app import db
from sqlalchemy import Table, Column, Integer, String, DateTime
from sqlalchemy.orm import mapper


class SASIFile(object):
    def __init__(self, id=None, path=None, filename=None, category=None,
                 size=None, created=None):
        self.id = id
        self.path = path
        self.filename = filename
        self.category = category
        self.size = size
        self.created = created

table = Table('sasi_file', db.metadata,
              Column('id', Integer, primary_key=True),
              Column('path', String),
              Column('filename', String),
              Column('category', String),
              Column('size', Integer),
              Column('created', DateTime),
             )

mapper(SASIFile, table)
