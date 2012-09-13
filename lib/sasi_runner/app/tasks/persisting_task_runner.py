""" Runs a task and persists its status updates. """
from functools import wraps


class PersistingTaskRunner(object):
    def __init__(self, task=None, dao=None):
        self.task = task
        self.dao = dao

        @wraps(f)
        def update_status_wrapper(*args, **kwargs):
            f(*args, **kwargs)
            # Do persistence stuff here.
        
        self.task.update_status = update_status_wrapper(
            self.task.update_status)

    def call():
        try:
            self.task.call()
        except:
            # Handle errors here.
            pass
