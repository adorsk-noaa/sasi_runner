"""
Task for running SASI.
"""

from sasi_data.dao.sasi_sa_dao import SASI_SqlAlchemyDAO
from sasi_data.ingestors.sasi_ingestor import SASI_Ingestor
from sasi_runner import packagers as packagers
from sasi_model.sasi_model import SASI_Model
import sasipedia
import task_manager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import tempfile
import os
import shutil
import zipfile
import logging


class LoggerLogHandler(logging.Handler):
    """ Custom log handler that logs messages to another
    logger. This can be used to chain together loggers. """
    def __init__(self, logger=None, **kwargs):
        logging.Handler.__init__(self, **kwargs)
        self.logger = logger

    def emit(self, record):
        self.logger.log(record.levelno, self.format(record))

class RunSasiTask(task_manager.Task):

    def __init__(self, input_path=None, output_file=None, config={}, 
                 get_connection=None, **kwargs):
        super(RunSasiTask, self).__init__(**kwargs)
        self.logger.debug("RunSasiTask.__init__")
        if not kwargs.get('data', None):
            self.data = {}
        self.input_path = input_path
        self.config = config

        if not output_file:
            os_hndl, output_file = tempfile.mkstemp(suffix=".georefine.tar.gz")
        self.output_file = output_file

        # Assign get_session function.
        if not get_connection:
            def get_connection():
                engine = create_engine('sqlite://')
                return engine.connect()
        self.get_connection = get_connection

        self.message_logger = logging.getLogger("Task%s_msglogger" % id(self))
        main_log_handler = LoggerLogHandler(self.logger)
        main_log_handler.setFormatter(
            logging.Formatter('%(message)s'))
        self.message_logger.addHandler(main_log_handler)
        self.message_logger.setLevel(self.logger.level)

    def call(self):
        self.progress = 1
        self.message_logger.info("Starting...")

        # Create build dir.
        build_dir = tempfile.mkdtemp(prefix="rsBuild.")

        con = self.get_connection()
        trans = con.begin()
        session = sessionmaker()(bind=con)

        # If input_path is a file, assemble data dir.
        if os.path.isfile(self.input_path):
            data_dir = tempfile.mkdtemp(prefix="run_sasi.")
            with zipfile.ZipFile(self.input_path, 'r') as zfile:
                zfile.extractall(data_dir)
        else:
            data_dir = self.input_path

        # @TODO: add validation here?

        # Read in data.
        try:
            base_msg = "Ingesting..."
            ingest_logger = self.get_logger_for_stage('ingest', base_msg)
            self.message_logger.info(base_msg)
            dao = SASI_SqlAlchemyDAO(session=session)
            sasi_ingestor = SASI_Ingestor(dao=dao, logger=ingest_logger,
                                          config=self.config.get('ingest', {}))
            sasi_ingestor.ingest(data_dir=data_dir)
        except Exception as e:
            self.logger.exception("Error ingesting")
            raise e

        # Run the model.
        try:
            base_msg = "Starting model run..."
            run_model_logger = self.get_logger_for_stage('run_model', base_msg)
            self.message_logger.info(base_msg)
            run_model_config = self.config.get('run_model', {})
            parameters = dao.query('__ModelParameters').one()

            taus = {}
            omegas = {}
            for i in range(0,4):
                taus[i] = getattr(parameters, "t_%s" % i)
                omegas[i] = getattr(parameters, "w_%s" % i)

            m = SASI_Model(
                t0=parameters.time_start,
                tf=parameters.time_end,
                dt=parameters.time_step,
                taus=taus,
                omegas=omegas,
                dao=dao,
                logger=run_model_logger,
                config=run_model_config,
            )
            m.run(commit_interval=run_model_config['commit_interval'])
        except Exception as e:
            self.logger.exception("Error running model: %s" % e)
            raise e

        # Generate metadata.
        try:
            base_msg = "Generating metadata..."
            metadata_logger = self.get_logger_for_stage('metadata', base_msg)
            self.message_logger.info(base_msg)
            metadata_dir = os.path.join(build_dir, "metadata")
            os.mkdir(metadata_dir)
            sasipedia.generate_sasipedia(targetDir=metadata_dir, dataDir=data_dir)
        except Exception as e:
            self.logger.exception("Error generating metadata.")
            raise e

        # Create georefine package.
        try:
            base_msg = "Generating GeoRefine package..."
            georefine_package_logger = self.get_logger_for_stage(
                'georefine_package', base_msg)
            self.message_logger.info(base_msg)
            georefine_package_file = self.get_output_package(
                data_dir=data_dir, 
                metadata_dir=metadata_dir,
                dao=dao, 
                output_format='georefine',
                logger=georefine_package_logger,
                output_file=self.output_file,
            )
        except Exception as e:
            self.logger.exception("Error generating georefine package.")
            raise e

        shutil.rmtree(build_dir)

        self.progress = 100
        self.message_logger.info("SASI Run completed, output file is:'%s'" % (
            self.output_file))
        self.status = 'resolved'

    def get_output_package(self, data_dir=None, metadata_dir=None, dao=None,
                           output_format=None, logger=logging.getLogger(),
                           batch_size=1e5,output_file=None):

        #self.engine_logger.setLevel(logging.INFO)

        # Assemble data for packager.
        data = {}
        data_categories = ['cell', 'energy', 'substrate', 'feature', 'gear',
                           'result']
        for category in data_categories:
            items_q = dao.query('__' + category.capitalize(),
                                format_='query_obj')
            batched_items = dao.orm_dao.get_batched_results(items_q, batch_size)
            data[category] = {
                'items': batched_items,
                'num_items': items_q.count()
            }

        if output_format == 'georefine':
            packager = packagers.GeoRefinePackager(
                data=data,
                source_data_dir=data_dir,
                metadata_dir=metadata_dir,
                logger=logger,
                output_file=output_file,
            )
        package_file = packager.create_package()
        return package_file

    def get_logger_for_stage(self, stage_id=None, base_msg=None):
        logger = logging.getLogger("%s_%s" % (id(self), stage_id))
        formatter = logging.Formatter(base_msg + ' %(message)s.')
        log_handler = LoggerLogHandler(self.message_logger)
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)
        logger.setLevel(self.message_logger.level)
        return logger

