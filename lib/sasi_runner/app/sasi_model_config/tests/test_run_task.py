import unittest
from sasi_runner.app.test.db_testcase import DBTestCase
from sasi_runner.app import db
from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
from sasi_runner.app.sasi_model_config.util.tests import config_setup as config_setup 
from sasi_runner.app.sasi_model_config.util import tasks as tasks
import time

from flask import json, url_for

import tempfile
import re


class RunConfigTest(DBTestCase):

    def get_engine_uri(self):
        hndl, dbfile = tempfile.mkstemp(prefix="rct.", suffix=".sqlite")
        return  'sqlite:///%s?check_same_thread=False' % dbfile

    def setUp(self):
        super(RunConfigTest, self).setUp()
        db.clear_db(bind=self.connection)
        db.init_db(bind=self.connection)
        self.base_path = '/config'

    def test_run_config_task(self):
        config = config_setup.generate_config()
        db.session.add(config)
        db.session.commit()
        path = "%s/%s/run" % (
            self.base_path, 
            config.id
        )
        output_format = "georefine"
        form_data = {
            'output_format': output_format
        }
        with self.client as c:
            r = self.client.post(path, data=form_data)
            loc = r.headers['location']
            match = re.search('run_status/(.*)/', loc)
            if match:
                task_id = int(match.group(1))
                task = tasks.get_task(task_id)
                status_path = "%s/task_status/%s" % (
                    self.base_path, task_id)
                while task.status['code'] != 'complete':
                    r = c.get(status_path)
                    print r.data
                    print "task running, status: ", task.status
                    time.sleep(1)
                r = c.get(status_path)
                print r.data
                    r = c.get(status_path)
                print "task complete, status: ", task.status

if __name__ == '__main__':
    unittest.main()
