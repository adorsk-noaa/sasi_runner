import sasi_runner.app.db as db
import sasi_runner.app.sasi_model_config.models as smc_models
import sasi_runner.app.sasi_model_config.util.tasks as tasks
from sasi_data.dao.sasi_sa_dao import SASI_SqlAlchemyDAO
from sasi_data.ingestors.sasi_ingestor import SASI_Ingestor
import tempfile
import zipfile
import sasipedia

import os


class RunConfigTask(tasks.Task):
    def __init__(self, config=None):
        super(RunConfigTask, self).__init__()
        self.config = config

    def run(self):
        # Validate config.
        # @TODO: Add this in later.
        #try:
            #validation.validate_config(self.config)
        #except e:
            #self.update_status(
                #code='failed', 
                #data=[
                    #{'type': 'error', 'value': "%s" % e}
                #]
            #)
            #return

        # Make temp data dir.
        data_dir= tempfile.mkdtemp(prefix="sasi_test.")
        print "data_dir is: ", data_dir

        # Unpack config files to tmp dir.
        for file_attr in smc_models.file_attrs:
            sasi_file = getattr(self.config, file_attr)
            if sasi_file:
                zfile = zipfile.ZipFile(sasi_file.path)
                zfile.extractall(data_dir)

        # Make target dir.
        target_dir = tempfile.mkdtemp(prefix="sasi_target")
        print "target dir is: ", target_dir

        # Generate metadata.
        metadata_dir = os.path.join(target_dir, "metadata")
        os.mkdir(metadata_dir)
        sasipedia.generate_sasipedia(targetDir=metadata_dir, dataDir=data_dir)

        # Setup SASI DAO.
        dao = SASI_SqlAlchemyDAO(session=db.session)

        # Ingest data.
        sasi_ingestor = SASI_Ingestor(dao=dao)
        sasi_ingestor.ingest(data_dir=data_dir)

        for c in dao.query('{{Cell}}'):
            print c

        # Generate model results.
        # Format results and metadata per output format.
        # Create results object.
        # Generate results link.
        return

def get_run_config_task(config):
    return RunConfigTask(config)
