import sasi_runner.app.db as db
import sasi_runner.app.sasi_model_config.models as smc_models
import sasi_runner.app.sasi_model_config.util.tasks as tasks
import sasi_runner.app.sasi_model_config.util.packagers as smc_packagers
from sasi_data.dao.sasi_sa_dao import SASI_SqlAlchemyDAO
from sasi_data.ingestors.sasi_ingestor import SASI_Ingestor
from sasi_model.sasi_model import SASI_Model
import tempfile
import zipfile
import sasipedia

import os


class RunConfigTask(tasks.Task):
    def __init__(self, config=None, output_format=None):
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

        # Unpack config files to tmp dir.
        for file_attr in smc_models.file_attrs:
            sasi_file = getattr(self.config, file_attr)
            if sasi_file:
                zfile = zipfile.ZipFile(sasi_file.path)
                zfile.extractall(data_dir)

        # Make target dir.
        target_dir = tempfile.mkdtemp(prefix="sasi_target")

        # Generate metadata.
        metadata_dir = os.path.join(target_dir, "metadata")
        os.mkdir(metadata_dir)
        sasipedia.generate_sasipedia(targetDir=metadata_dir, dataDir=data_dir)

        # Setup SASI DAO.
        dao = SASI_SqlAlchemyDAO(session=db.session)

        # Ingest data.
        sasi_ingestor = SASI_Ingestor(dao=dao)
        sasi_ingestor.ingest(data_dir=data_dir)

        # Setup model.
        parameters = dao.query('{{ModelParameters}}').one()
        cells = dao.query('{{Cell}}').all()
        substrates = dao.query('{{Substrate}}').all()
        features = dao.query('{{Feature}}').all()
        gears = dao.query('{{Gear}}').all()
        vas = dao.query('{{VA}}').all()
        efforts = dao.query('{{Effort}}').all()

        taus = {}
        omegas = {}
        for i in range(1,4):
            taus[i] = getattr(parameters, "t_%s" % i)
            omegas[i] = getattr(parameters, "w_%s" % i)

        m = SASI_Model(
            t0=parameters.time_start,
            tf=parameters.time_end,
            dt=parameters.time_step,
            taus=taus,
            omegas=omegas,
            cells=cells,
            features=features,
            efforts=efforts,
            vas=vas,
            opts={'verbose': True}
        )

        # Run the model.
        m.run()

        # Save the results.
        #dao.save_all(m.results)

        # Format output package.
        format_output_package(config, dao, output_format)

        # Create results object.
        # Generate results link.
        return

def format_output_package(config=None, dao=None, output_format=None):
    packager = None
    if output_format == 'georefine':
        packager = smc_packagers.GeoRefinePackager()
    packager.create_package()

def get_run_config_task(config):
    return RunConfigTask(config)
