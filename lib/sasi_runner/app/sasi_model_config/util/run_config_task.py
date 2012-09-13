from sasi_runner.app import db as db
from sasi_runner.app.sasi_file import models as sf_models
from sasi_runner.app.sasi_file import views as sf_views
from sasi_runner.app.sasi_model_config import models as smc_models
from sasi_runner.app.sasi_result import models as sr_models
from sasi_runner.app.sasi_model_config.util import tasks as tasks
from sasi_runner.app.sasi_model_config.util import packagers as smc_packagers
from sasi_data.dao.sasi_sa_dao import SASI_SqlAlchemyDAO
from sasi_data.ingestors.sasi_ingestor import SASI_Ingestor
from sasi_model.sasi_model import SASI_Model
import tempfile
import zipfile
import sasipedia
from datetime import datetime
import os
import shutil


class RunConfigTask(tasks.Task):
    def __init__(self, config_id=None, output_format=None):
        super(RunConfigTask, self).__init__()
        self.config_id = config_id
        self.output_format = output_format

    def run(self):
        # Note: need to load config here, to avoid session/threading issues.
        self.config = db.session.query(smc_models.SASIModelConfig)\
                .get(self.config_id)

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
        data_dir = tempfile.mkdtemp(prefix="sasi_test.")

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

        # Create output package.
        tmp_package_file = get_output_package(
            data_dir=data_dir, 
            dao=dao, 
            output_format=self.output_format
        )

        # Save the output package to the data dir.
        #@TODO: GET THIS FROM CONFIG!
        package_file_name = "%s.georefine_results.tar.gz" % self.config.title
        files_dir = sf_views.uploads_dest
        perm_package_file = os.path.join(files_dir, package_file_name)
        shutil.move(tmp_package_file, perm_package_file)

        # Create results object.
        package_size = os.stat(perm_package_file).st_size
        result_file = sf_models.SASIFile(
            filename=package_file_name,
            category="%s results" % self.output_format,
            path=perm_package_file,
            size=package_size,
            created=datetime.utcnow()
        )
        sasi_result = sr_models.SASIResult(
            title="Da Title", 
            result_file=result_file
        )
        db.session.add(sasi_result)
        db.session.commit()

        # Save result file id to task data.
        self.update_status(
            code='complete', 
            data={'result_id': sasi_result.id}
        )

def get_output_package(data_dir="", dao=None, output_format=None):
    packager = None
    cells = dao.query('{{Cell}}')
    energys = dao.query('{{Energy}}')
    substrates = dao.query('{{Substrate}}')
    features = dao.query('{{Feature}}')
    gears = dao.query('{{Gear}}')
    results = dao.query('{{Result}}')

    if output_format == 'georefine':
        packager = smc_packagers.GeoRefinePackager(
            cells=cells,
            energys=energys,
            substrates=substrates,
            features=features,
            gears=gears,
            results=results,
            source_data_dir=data_dir
        )
    package_file = packager.create_package()
    return package_file
