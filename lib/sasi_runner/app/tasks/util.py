""" Task utilities. """
from sasi_runner.app import db as db
from sasi_runner.app.tasks.models import Task
import functools
import types
import futures

def get_task(task_id):
    task = db.session.query(Task).get(task_id)
    return task

def makeTaskPersistent(task):

    # Wrap functions for persistence.
    def persistence_wrapper(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            func(*args, **kwargs)
            if kwargs.get('commit', True):
                # Note: need to merge for compatibility w/ threading. 
                db.session.merge(self)
                db.session.commit()
        return wrapper

    task.set_status = types.MethodType(
        persistence_wrapper(task.set_status), task)

    task.set_data = types.MethodType(
        persistence_wrapper(task.set_data), task)

    # Do initial persistence.
    db.session.add(task)
    db.session.commit()

def execute_task(task):
    executor = futures.ThreadPoolExecutor(max_workers=5)
    task.set_status('running')
    future = executor.submit(task.call)
    executor.shutdown(wait=False)
    def on_future_done(future_):
        # Note: need to merge for compatibility w/ threading. 
        db.session.merge(task)
        e = future_.exception()
        if e:
            task.data['error'] = "Error: %s" % e
            task.set_data(task.data)
            task.set_status('rejected')
        else:
            task.set_status('resolved')

    future.add_done_callback(on_future_done)
    return future

