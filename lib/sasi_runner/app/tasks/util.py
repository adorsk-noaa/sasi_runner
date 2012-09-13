""" Task utilities. """
from sasi_runner.app import db as db
import functools
import types


def makeTaskPersistent(task, dao=None):

    # Wrap functions for persistence.
    def persistence_wrapper(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            if kwargs.get('commit'):
                db.session.add(self)
                db.session.commit()
        return wrapper

    task.set_status = persistence_wrapper(task.set_status)
    task.set_data = persistence_wrapper(task.set_data)

    # Do initial persistence.
    db.session.add(task)
    db.session.commit()
