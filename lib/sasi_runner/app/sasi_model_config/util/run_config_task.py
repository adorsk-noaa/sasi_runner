from sasi_runner.app.tasks import models as tasks_models
from sasi_runner.app import db as db
from sasi_runner.app.sasi_file import models as sf_models
from sasi_runner.app.sasi_file import views as sf_views
from sasi_runner.app.sasi_model_config import models as smc_models
from sasi_runner.app.sasi_result import models as sr_models
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
import sys
from sqlalchemy.orm import sessionmaker


def get_run_config_task(config_id=None, output_format=None):

    """ Return a task which runs a config. """
    def call(self):
        """ The task's call method. 'self' is the task object. """
        try:
            # Add transaction stuff here.
            run_connection = db.session().connection().engine.connect()
            run_trans = run_connection.begin()
            run_sessionmaker = sessionmaker()
            run_session = run_sessionmaker(bind=run_connection)

            # Run the config.
            runner = ConfigRunner(
                run_session=run_session,
                config_id=config_id,
                output_format=output_format,
                task=self
            )
            runner.run_config()

            run_session.close()

        # Rollback session if there was an error.
        except Exception as e:
            import traceback
            print '-' * 60
            traceback.print_exc(file=sys.stdout)
            print '-' * 60
            run_trans.rollback()
            raise e


    return tasks_models.Task(call=call)

class ConfigRunner(object):
    def __init__(self, run_session=None, config_id=None, output_format=None, task=None):
        self.run_session = run_session
        self.config_id = config_id
        self.output_format = output_format
        self.task = task

    def run_config(self):
        # Note: need to load config here, to avoid session/threading issues.
        self.config = db.session().query(smc_models.SASIModelConfig)\
                .get(self.config_id)

        # Initialize task data.
        # For the run config task, data will consist of a set
        # of 'stages', representing the state of subtasks within
        # the task.
        # @TODO; rename for better semantics?  Queue?
        task_data = {}
        stages = {}
        task_data['stages'] = stages

        # Validate config.
        stages['validating'] = {'status': {'code': 'running'}}
        self.task.set_data(task_data)
        try:
            # @TODO: Add this in later.
            pass
            #validation.validate_config(self.config)
            stages['validating']['status']['code'] = 'resolved'
            self.task.set_data(task_data)
        except Exception as e:
            stages['validating']['status']['code'] = 'rejected'
            self.task.set_data(task_data)
            raise e


        # Unpack input files to tmp dir.
        stages['unpacking'] = {'status': {'code': 'running'}}
        self.task.set_data(task_data)
        try:
            data_dir = tempfile.mkdtemp(prefix="sasi_test.")
            for file_attr in smc_models.file_attrs:
                sasi_file = getattr(self.config, file_attr)
                if sasi_file:
                    zfile = zipfile.ZipFile(sasi_file.path)
                    zfile.extractall(data_dir)
            stages['unpacking']['status']['code'] = 'resolved'
            self.task.set_data(task_data)
        except Exception as e:
            stages['unpacking']['status']['code'] = 'rejected'
            self.task.set_data(task_data)
            raise e

        # Read files.
        stages['reading'] = {'status': {'code': 'running'}}
        self.task.set_data(task_data)
        try:
            dao = SASI_SqlAlchemyDAO(session=self.run_session)
            sasi_ingestor = SASI_Ingestor(dao=dao)
            sasi_ingestor.ingest(data_dir=data_dir)
            stages['reading']['status']['code'] = 'resolved'
            self.task.set_data(task_data)
        except Exception as e:
            stages['reading']['status']['code'] = 'rejected'
            self.task.set_data(task_data)
            raise e

        # Run the model.
        stages['model'] = {'status': {'code': 'running'}}
        self.task.set_data(task_data)
        try:
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
            m.run()
            stages['model']['status']['code'] = 'resolved'
            self.task.set_data(task_data)
        except Exception as e:
            stages['model']['status']['code'] = 'rejected'
            self.task.set_data(task_data)
            raise e

        # Save the results.
        stages['results'] = {'status': {'code': 'running'}}
        self.task.set_data(task_data)
        try:
            dao.save_all(m.results)
            stages['results']['status']['code'] = 'resolved'
            self.task.set_data(task_data)
        except Exception as e:
            stages['results']['status']['code'] = 'rejected'
            self.task.set_data(task_data)
            raise e

        # Generate metadata.
        stages['metadata'] = {'status': {'code': 'running'}}
        self.task.set_data(task_data)
        try:
            target_dir = tempfile.mkdtemp(prefix="sasi_target")
            stages['metadata'] = {'status': {'code': 'running'}}
            metadata_dir = os.path.join(target_dir, "metadata")
            os.mkdir(metadata_dir)
            sasipedia.generate_sasipedia(targetDir=metadata_dir, dataDir=data_dir)
            stages['metadata']['status']['code'] = 'resolved'
            self.task.set_data(task_data)
        except e:
            stages['metadata']['status']['code'] = 'rejected'
            self.task.set_data(task_data)
            raise e

        # Create output package.
        stages['formatting'] = {'status': {'code': 'running'}}
        self.task.set_data(task_data)
        try:
            tmp_package_file = self.get_output_package(
                data_dir=data_dir, 
                dao=dao, 
                output_format=self.output_format
            )
            stages['formatting']['status']['code'] = 'resolved'
            self.task.set_data(task_data)
        except Exception as e:
            stages['formatting']['status']['code'] = 'rejected'
            self.task.set_data(task_data)
            raise e

        # Save the output package to the data dir.
        #@TODO: GET THIS FROM CONFIG!
        stages['assembling'] = {'status': {'code': 'running'}}
        self.task.set_data(task_data)
        try:
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

            # Save the result to the app db session, 
            # rather than the local run session.
            # Otherwise it will not be commited.
            app_session = db.session()
            app_session.add(sasi_result)
            app_session.commit()

            # Save result file id to task data.
            task_data['result'] = sasi_result.to_dict()
            self.task.set_data(task_data)

            stages['assembling']['status']['code'] = 'resolved'
            self.task.set_data(task_data)
        except Exception as e:
            stages['assembling']['status']['code'] = 'rejected'
            self.task.set_data(task_data)
            raise e

    def get_output_package(self, data_dir="", dao=None, output_format=None):
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
