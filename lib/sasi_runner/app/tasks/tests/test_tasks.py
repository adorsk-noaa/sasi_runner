import unittest
from sasi_runner.app.test.db_testcase import DBTestCase
from sasi_runner.app import db
from sasi_runner.app.tasks import models as tasks_models
from sasi_runner.app.tasks import util as tasks_util
import tempfile
import time
import sys


class TaskTest(DBTestCase):

    def get_engine_uri(self):
        hndl, dbfile = tempfile.mkstemp(prefix="tasks.", suffix=".sqlite")
        return  'sqlite:///%s?check_same_thread=False' % dbfile

    def setUp(self):
        super(TaskTest, self).setUp()
        db.clear_db(bind=self.connection)
        db.init_db(bind=self.connection)

    def test_task(self):
        task = self.get_dummy_task()
        task.call()
        assert task.data == "testing"
        assert task.status == "testing"

    def test_persistent_task(self):
        task = self.get_dummy_task()
        tasks_util.makeTaskPersistent(task)
        assert task.id == 1
        task.call()
        queried_task = db.session.query(tasks_models.Task).get(1)
        assert queried_task.data == 'testing'
        assert queried_task.status == 'testing'

    def test_execute_task(self):
        task = self.get_long_task()
        future = tasks_util.execute_task(task)
        while not future.done():
            time.sleep(1)

    def get_dummy_task(self):
        def call(self):
            self.set_data('testing')
            self.set_status("testing")
        return tasks_models.Task(call=call)

    def get_long_task(self):
        def call(self):
            self.set_status('running')
            for i in range(5):
                print >> sys.stderr, "i is: ", i
                self.set_data(i)
                time.sleep(1)
            self.set_status('complete')
        return tasks_models.Task(call=call)

if __name__ == '__main__':
    unittest.main()
