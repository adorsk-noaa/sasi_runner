import unittest
from sasi_runner.app.tasks import models as tasks_models
from sasi_runner.app.tasks import util as tasks_util


class TaskTest(unittest.TestCase):

    def test_task(self):
        task = self.get_dummy_task()
        task.call()
        assert task.status == "testing"

    def test_persistent_task(self):
        task = self.get_dummy_task()
        tasks_util.makeTaskPersistent(task)
        print task.id
        task.call()
        assert task.status == "testing"

    def get_dummy_task(self):
        def call(self):
            self.set_status("testing")
        return tasks_models.Task(call=call)

if __name__ == '__main__':
    unittest.main()
