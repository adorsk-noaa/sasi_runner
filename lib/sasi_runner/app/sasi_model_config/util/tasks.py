from threading import Thread
import time


registry = {}

def get_task(task_id):
    global registry
    return registry.get(task_id)

def delete_task(task_id):
    global registry
    if registry.has_key(task_id):
        del registry[task_id]

class Task(Thread):
    def __init__(self):
        global registry
        self.id = id(self)
        self.status = {
            'code': None,
            'data': None,
            'modified': None
        }
        registry[self.id] = self

        Thread.__init__(self)

    def update_status(self, code=None, data=None):
        self.status['code'] = code
        self.status['data'] = data
        self.status['modified'] = time.time()
