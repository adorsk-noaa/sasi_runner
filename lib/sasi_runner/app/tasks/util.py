""" Task utilities. """
from sasi_runner.app import db as db
from sasi_runner.app.tasks.models import Task
import functools
import types
import futures

def get_task(task_id):
    task = db.session().query(Task).get(task_id)
    return task

def makeTaskPersistent(task):

    # Wrapper to set up session for task.
    def call_wrapper(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            session = db.session()
            if not self in session:
                session.add(self)
            try:
                func(*args, **kwargs)
            except Exception as e:
                session.close()
                raise e
        return wrapper

    task.call = types.MethodType(
        call_wrapper(task.call), task)

    # Wrapper to add commits for persistence.
    def commit_wrapper(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            func(*args, **kwargs)
            if kwargs.get('commit', True):
                session = db.session()
                if not self in session:
                    session.add(self)
                session.commit()
        return wrapper

    task.set_status = types.MethodType(
        commit_wrapper(task.set_status), task)

    task.set_data = types.MethodType(
        commit_wrapper(task.set_data), task)

    # Do initial persistence.
    session = db.session()
    session.add(task)
    session.commit()

def execute_task(task):
    executor = futures.ThreadPoolExecutor(max_workers=5)
    future = executor.submit(task.call)
    executor.shutdown(wait=False)
    def on_future_done(future_, task=task):
        # Check session for compatibility w/ threading. 
        session = db.session()
        if not task in session:
            session.add(task)
        try:
            e = future_.exception()
            if e:
                set_task_error(task, str(e))
            else:
                task.set_status('resolved')
        except Exception as e:
            set_task_error(task, str(e))

    future.add_done_callback(on_future_done)
    return future

def set_task_error(task, error_msg):
    task.data['error'] = "Error: %s" % error_msg
    task.set_data(task.data)
    task.set_status('rejected')
