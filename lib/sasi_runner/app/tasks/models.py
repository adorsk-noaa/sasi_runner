""" Task models. """
import types
from sasi_runner.app import db 
from sqlalchemy import Table, Column, Integer, String, PickleType
from sqlalchemy.orm import mapper
import functools
import types


class Task(object):
    """ Task object. Represents a unit of work. """
    def __init__(self, call=None):
        self.status = 'pending'
        self.data = {}
        if not call:
            def call_stub(self): pass
            call = call_stub

        # Wrap call to include pre_run method.
        def call_wrapper(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                self.pre_run()
                func(self, *args, **kwargs)
            return wrapper

        self.call = types.MethodType(call_wrapper(call), self)

    def pre_run(self):
        self.set_status('running')

    def set_status(self, status, *args, **kwargs):
        self.status = status

    def set_data(self, data, *args, **kwargs):
        self.data = data

table = Table('tasks', db.metadata,
              Column('id', Integer, primary_key=True),
              Column('status', String),
              Column('data', PickleType(mutable=True)),
             )
mapper(Task, table)
