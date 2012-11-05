"""
Command-line utility for
executing a SASI run.
"""

from sasi_data.dao.sasi_sa_dao import SASI_SqlAlchemyDAO
from sasi_data.ingestors.sasi_ingestor import SASI_Ingestor
from sasi_runner.app import db as db
from sasi_runner.app.sasi_model_config.util import packagers as smc_packagers
from sasi_model.sasi_model import SASI_Model
import sasipedia
import argparse
import json
import tempfile
import os
import shutil
import zipfile
from sqlalchemy.orm import sessionmaker


# Setup argument handling.
argparser = argparse.ArgumentParser(description='Run SASI model.')
argparser.add_argument('-c', required=True, help='config file')
argparser.add_argument('-o', help='output file')
argparser.add_argument('-f', help='output format')

def main():
    # Read args.
    args = argparser.parse_args()
    config_file = args.c
    config = json.load(open(config_file, 'rb'))

    output_file = args.o or config.get('output_file')
    output_format = args.f or config.get('output_format') or 'georefine'
    input_files = config['input_files']

    run_sasi(
        config=config,
        output_file=output_file,
        output_format=output_format
    )

def run_sasi(input_files=None, output_file=None, output_format=None):


    # Create build dir.
    build_dir = tempfile.mkdtemp(prefix="rsBuild.")

    # Get transactional session.
    connection = db.session().connection().engine.connect()
    trans = connection.begin()
    session = sessionmaker(bind=connection)()

    # Assemble data dir from file.
    data_dir = tempfile.mkdtemp(prefix="run_sasi.")
    for category, input_file in input_files.items():
        with zipfile.ZipFile(input_file, 'r') as zfile:
            zfile.extractall(data_dir)

    # @TODO: add validation here?

    # Read in data.
    try:
        dao = SASI_SqlAlchemyDAO(session=session)
        sasi_ingestor = SASI_Ingestor(dao=dao)
        sasi_ingestor.ingest(data_dir=data_dir)
    except Exception as e:
        raise e

    # Run the model.
    try:
        parameters = dao.query('__ModelParameters').one()
        cells = dao.query('__Cell').all()
        substrates = dao.query('__Substrate').all()
        features = dao.query('__Feature').all()
        gears = dao.query('__Gear').all()
        vas = dao.query('__VA').all()
        efforts = dao.query('__Effort').all()
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
    except Exception as e:
        raise e

    # Save the results.
    try:
        dao.save_dicts('Result', m.results, verbose=True)
    except Exception as e:
        raise e

    # Generate metadata.
    try:
        metadata_dir = os.path.join(build_dir, "metadata")
        os.mkdir(metadata_dir)
        sasipedia.generate_sasipedia(targetDir=metadata_dir, dataDir=data_dir)
    except Exception as e:
        raise e

    # Create output package.
    try:
        tmp_package_file = get_output_package(
            data_dir=data_dir, 
            metadata_dir=metadata_dir,
            dao=dao, 
            output_format=output_format
        )
    except Exception as e:
        raise e

    # Move the output package to the output_file path.
    shutil.move(tmp_package_file, output_file)

def get_output_package(data_dir=None, metadata_dir=None, dao=None, output_format=None):
    cells = dao.query('__Cell')
    energies = dao.query('__Energy')
    substrates = dao.query('__Substrate')
    features = dao.query('__Feature')
    gears = dao.query('__Gear')
    results = dao.query('__Result')

    if output_format == 'georefine':
        packager = smc_packagers.GeoRefinePackager(
            cells=cells,
            energies=energies,
            substrates=substrates,
            features=features,
            gears=gears,
            results=results,
            source_data_dir=data_dir,
            metadata_dir=metadata_dir
        )
    package_file = packager.create_package()
    return package_file

if __name__ == '__main__':
    main()
