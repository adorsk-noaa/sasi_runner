""" Task object.  Represents a unit of work to be performed. """
class Task(object):
    def __init__(self):
        self.status = {}

    def set_status(self, status):
        self.status = status

    def call(self):
        pass

