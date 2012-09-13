""" Task utilities for asynchronous execution. """
import functools
import types

class Task(object):
    """ Task object. Represents a unit of work. """
    def __init__(self, call=None):
        self.status = {}
        if not call:
            def call_stub(self): pass
            call = call_stub
        self.call = types.MethodType(call, self)

    def set_status(self, status=None, **kwargs):
        self.status = status

def makeTaskPersistent(task, dao=None):

    def wrap_set_status(set_status_func):
        @functools.wraps(set_status_func)
        def wrapper(persist=True, *args, **kwargs):
            set_status_func(*args, **kwargs)
            if persist:
                # Do persistence stuff here.
                pass
        return wrapper
    new_set_status = wrap_set_status(task.set_status)
    task.set_status = types.MethodType(new_set_status, task)

    # Do initial persistence.
    task.id = id(task)
