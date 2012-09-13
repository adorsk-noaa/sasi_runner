""" Task models. """
import types
from sasi_runner.app import db 
from sqlalchemy import Table, Column, Integer, String, PickleType
from sqlalchemy.orm import mapper


class Task(object):
    """ Task object. Represents a unit of work. """
    def __init__(self, call=None):
        self.status = "uninitialized"
        self.data = None
        if not call:
            def call_stub(self): pass
            call = call_stub
        self.call = types.MethodType(call, self)

    def set_status(self, status):
        self.status = status

    def set_data(self, data):
        self.data = data

table = Table('tasks', db.metadata,
              Column('id', Integer, primary_key=True),
              Column('status', String),
              Column('data', PickleType),
             )
mapper(Task, table)
