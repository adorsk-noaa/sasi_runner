"""
Task for running SASI.
"""

from sasi_data.dao.sasi_sa_dao import SASI_SqlAlchemyDAO
from sasi_data.ingestors.sasi_ingestor import SASI_Ingestor
from sasi_runner import packagers as packagers
from sasi_runner.sasi_model import SASI_Model
import sasipedia
import task_manager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import tempfile
import os
import shutil
import zipfile
import logging
import platform


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

        # Set default result key fields.
        # Can include any members of:
        # 'gear_id', 'substrate_id', 'energy_id', 'feature_id',
        # 'feature_category_id'
        self.config.setdefault('result_fields', ['gear_id'])

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
            sasi_ingestor = SASI_Ingestor(
                data_dir=data_dir, dao=dao, logger=ingest_logger,
                config=self.config.get('ingest', {})
            )
            sasi_ingestor.ingest()
        except Exception as e:
            self.logger.exception("Error ingesting")
            raise e

        # Run the model.
        try:
            base_msg = "Running SASI model ..."
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
                'effort_model': parms.effort_model,
                'taus': taus,
                'omegas': omegas,
                'dao': dao,
                'logger': run_model_logger,
                'result_fields': self.config.get('result_fields'),
            }

            run_kwargs = {}
            run_kwargs.update(run_model_config.get('run', {}))
            batch_size = run_kwargs.setdefault('batch_size', 20)
            if batch_size == 'auto':
                run_kwargs['batch_size'] = self.get_run_batch_size(dao)

            model_kwargs.update(run_model_config)
            m = SASI_Model(**model_kwargs)
            m.run(**run_kwargs)
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

        # Generate ouput package.
        try:
            output_config = self.config.get('output', {})
            base_msg = "Generating output package..."
            output_package_logger = self.get_logger_for_stage(
                'output_package', base_msg)
            self.message_logger.info(base_msg)

            self.create_output_package(
                data_dir=data_dir, 
                metadata_dir=metadata_dir,
                dao=dao, 
                output_format='georefine',
                logger=output_package_logger,
                batch_size=output_config.get('batch_size', 'auto'),
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

    def create_output_package(self, data_dir=None, metadata_dir=None, dao=None,
                           output_format=None, logger=logging.getLogger(),
                           batch_size='auto',output_file=None):

        # Calculate batch size if set to 'auto'.
        if batch_size == 'auto':
            approx_obj_size = self.get_approx_sasi_obj_size()
            mem = self.get_free_mem()
            # Calculate rough batch size w/ some fudge.
            batch_size = max(1e3, int(.75 * mem/approx_obj_size))

        # Assemble data for packager.
        data = {}
        data_categories = ['cell', 'energy', 'substrate', 'feature_category', 
                           'feature', 'gear', 'result']
        for category in data_categories:
            source_name = ''.join([s.capitalize() for s in category.split('_')])
            items_q = dao.query('__' + source_name,
                                format_='query_obj')
            batched_items = dao.get_batched_results(items_q, batch_size)
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

    def get_run_batch_size(self, dao, max_memory=1e9):
        """ Calculate approximate number of cells to include
        in model batch runs.
        """

        approx_obj_size = self.get_approx_sasi_obj_size()
        mem = self.get_free_mem()

        # Get counts of SASI objects.
        parms = dao.query('__ModelParameters').one()
        counts = {}
        counts['t'] = (parms.time_end - parms.time_start)/parms.time_step
        data_categories = ['energy', 'substrate', 'feature', 'gear', 'cell']
        for category in data_categories:
            counts[category] = dao.query('__' + category.capitalize(), 
                                         format_='query_obj').count()

        # Estimate max number of results per cell, based on result key fields.
        result_fields_to_data_cats = {
            'energy_id': 'energy',
            'substrate_id': 'substrate',
            'feature_id': 'feature',
            'gear_id': 'gear'
        }
        results_per_c = counts['t']
        for field in self.config['result_fields']:
            data_cat = result_fields_to_data_cats[field]
            results_per_c *= counts[data_cat]

        # Estimate max number of efforts per cell.
        efforts_per_c = 1
        for data_cat in ['t', 'gear']:
            efforts_per_c *= counts[data_cat]

        # Estimate memory use per cell.
        total_size_per_c = (results_per_c + efforts_per_c) * approx_obj_size

        # Calculate batch size, w/ some fudging.
        batch_size = max(1, int(.75 * mem/total_size_per_c))
        return batch_size

    def get_approx_sasi_obj_size(self):
        """ Rough approximations of SASI object sizes
        in bytes. """
        if platform.system() == 'Java':
            return 2048.0
        else:
            return 1024.0

    def get_free_mem(self):
        """ Get available memory."""
        if platform.system() == 'Java':
            return self.get_jython_free_mem()
        else:
            return self.get_cython_free_mem()

    def get_jython_free_mem(self):
        # Force garbage collection first.
        from java.lang import Runtime
        from java.lang.ref import WeakReference
        from java.lang import Object
        from java.lang import System
        obj = Object()
        ref = WeakReference(obj)
        obj = None
        while ref.get() is not None:
            System.gc()

        # Calculate approx. available memory.
        return Runtime.getRuntime().freeMemory()

    def get_cython_free_mem(self):
        import ctypes
        if os.name == "posix":
            mbs = int(os.popen("free -m").readlines()[1].split()[3])
            return (1024**2) * mbs
        elif os.name == "nt":
            kernel32 = ctypes.windll.kernel32
            c_ulong = ctypes.c_ulong
            class MEMORYSTATUS(ctypes.Structure):
                _fields_ = [
                    ("dwLength", c_ulong),
                    ("dwMemoryLoad", c_ulong),
                    ("dwTotalPhys", c_ulong),
                    ("dwAvailPhys", c_ulong),
                    ("dwTotalPageFile", c_ulong),
                    ("dwAvailPageFile", c_ulong),
                    ("dwTotalVirtual", c_ulong),
                    ("dwAvailVirtual", c_ulong)
                ]
            memoryStatus = MEMORYSTATUS()
            memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUS)
            kernel32.GlobalMemoryStatus(ctypes.byref(memoryStatus))
            return int(memoryStatus.dwAvailPhys)
        else:
            raise Exception("Cannot detect memory for os '%s'" % os.name)
