""" Task decorators. """
from functools import wraps


def makeTaskPersistent(task=None):

    # Log status updates.
    @wraps(f)
    def update_status_wrapper(*args, **kwargs):
        f(*args, **kwargs)
        # Do persistence stuff here.
    
    task.update_status = update_status_wrapper(
        self.task.update_status)

    # Make db entry on task creation.
    @wraps(f)
    def call_wrapper(*args, **kwargs):
        # Do persistence stuff here.
        try:
            f(*args, **kwargs)
        except:
            # Handle errors here.
            pass
