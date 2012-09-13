import unittest
from sasi_runner.app.test.db_testcase import DBTestCase
from sasi_runner.app import db
from sasi_runner.app.tasks import models as tasks_models
from sasi_runner.app.tasks import util as tasks_util
import tempfile


class TaskTest(DBTestCase):

    def get_engine_uri(self):
        hndl, dbfile = tempfile.mkstemp(prefix="tasks.", suffix=".sqlite")
        return  'sqlite:///%s?check_same_thread=False' % dbfile

    def setUp(self):
        super(TaskTest, self).setUp()
        db.clear_db(bind=self.connection)
        db.init_db(bind=self.connection)

    def xtest_task(self):
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

    def get_dummy_task(self):
        def call(self):
            self.set_data('testing')
            self.set_status("testing")
        return tasks_models.Task(call=call)

if __name__ == '__main__':
    unittest.main()
