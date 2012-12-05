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
                 get_connection=None, max_mem=1e9, **kwargs):
        super(RunSasiTask, self).__init__(**kwargs)
        self.logger.debug("RunSasiTask.__init__")
        if not kwargs.get('data', None):
            self.data = {}
        self.input_path = input_path
        self.max_mem = max_mem
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
            parms = dao.query('__ModelParameters').one()

            taus = {}
            omegas = {}
            for i in range(0,4):
                taus[i] = getattr(parms, "t_%s" % i)
                omegas[i] = getattr(parms, "w_%s" % i)

            model_kwargs = {
                't0': parms.time_start,
                'tf': parms.time_end,
                'dt': parms.time_step,
                'taus': taus,
                'omegas': omegas,
                'dao': dao,
                'logger': run_model_logger,
            }

            if 'batch_size' not in run_model_config:
                # Just use a default batch size, rather than one calculated on
                # memory. After a certain size, limiting factor becomes write
                # speed, which doesn't vary much once batches are past a certain
                # size. In addition, smaller, regular batch sizes can make the
                # logging output easier for users to understand.
                #model_kwargs['batch_size'] = self.get_batch_size(dao, self.max_mem)
                model_kwargs['batch_size'] = 100

            model_kwargs.update(run_model_config)
            m = SASI_Model(**model_kwargs)
            m.run(**run_model_config.get('run',{}))
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

        # Special time data, to make time queries reasonable.
        parms = dao.query('__ModelParameters').one()
        class TimeObj(object):
            def __init__(self, id):
                self.id = id
        data['time'] = {
            'items': [TimeObj(t) for t in range(parms.time_start, 
                                                parms.time_end + 1,
                                                parms.time_step)]
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

    def get_batch_size(self, dao, max_memory=1e9):
        """ Calculate approximate number of results per cell,
        based on rough size of efforts + counts per cell.
        We can use this to set a reasonable batch size,
        based on the given max memory.
        """
        parms = dao.query('__ModelParameters').one()
        counts = {}
        counts['t'] = (parms.time_end - parms.time_start)/parms.time_step
        data_categories = ['energy', 'substrate', 'feature', 'gear',
                           'effort', 'cell']
        for category in data_categories:
            counts[category] = dao.query('__' + category.capitalize(), 
                                         format_='query_obj').count()
        # Approximate size of efforts per cell.
        e_size = 1024
        es_per_c = counts['effort']/counts['cell']
        e_size_per_c = e_size * es_per_c

        # approximate size of results per cell.
        r_size = 1024
        rs_per_c = 1
        for category in ['t', 'energy', 'substrate', 'feature', 'gear']:
            rs_per_c *= counts[category]
        r_size_per_c = r_size * rs_per_c

        total_size_per_c = e_size_per_c + r_size_per_c
        batch_size = max(1, int(max_memory/total_size_per_c))
        print "bs is: ", batch_size
        return batch_size
