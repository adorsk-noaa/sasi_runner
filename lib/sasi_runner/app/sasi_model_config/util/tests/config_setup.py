from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
import sasi_runner.app.sasi_model_config.util.validation as validation
from sasi_data.util.data_generators import generate_data_dir
import os
import tempfile
import zipfile


base_dir = os.path.dirname(os.path.abspath(__file__))
base_data_dir = os.path.join(base_dir, "test_data")

id_= 0
def get_id():
    global id_
    id_ += 1
    return id_

def zipdir(basedir, archivename):
    z = zipfile.ZipFile(archivename, "w", zipfile.ZIP_DEFLATED)
    basename = os.path.basename(basedir)
    for root, dirs, files in os.walk(basedir):
        for fn in files:
            absfn = os.path.join(root, fn)
            zfn = os.path.join(basename, absfn[len(basedir)+len(os.sep):])
            z.write(absfn, zfn)
    z.close()

def generate_config():

    config = SASIModelConfig(id=get_id(), title="tst_config")

    target_dir = tempfile.mkdtemp(prefix="ctest.")
    data_dir = generate_data_dir()
    for section in [
        'substrates', 
        'features', 
        'energies', 
        'gears',
        'va',
        'habitats',
        'grid',
        'model_parameters',
        'fishing_efforts',
        'georefine',
    ]:
        section_dir = os.path.join(data_dir, section)
        archivename = os.path.join(target_dir, "%s.zip" % section)
        zipdir(section_dir, archivename)
        setattr(config, section, SASIFile(
            id=get_id(),
            path=archivename,
            filename=section + ".zip",
            category=section,
            size=12345,
            created=None
        ))

    return config


def setUp_config_1():
    data_dir = os.path.join(base_data_dir, "config_1")
    config = SASIModelConfig(
        id=get_id(),
        title="config 1"
    )

    # Setup file sections.
    for section in [
        'substrates', 
        'features', 
        'energies', 
        'gears',
        'va',
        'habitats',
        'grid',
        'model_parameters',
        'fishing_efforts',
        'map_layers',
    ]:
        setattr(config, section, SASIFile(
            id=get_id(),
            path=os.path.join(data_dir, section + ".zip"),
            filename=section + ".zip",
            category=section,
            size=12345,
            created=None
        ))

    return config
