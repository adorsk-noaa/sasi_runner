""" Task utilities. """
from sasi_runner.app import db as db
from sasi_runner.app.tasks.models import Task
import functools
import types
import futures

def get_task(task_id):
    task = db.session.query(Task).get(task_id)
    return task

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

def execute_task(task):
    executor = futures.ThreadPoolExecutor(max_workers=5)
    future = executor.submit(task.call)
    executor.shutdown(wait=False)
    return future

