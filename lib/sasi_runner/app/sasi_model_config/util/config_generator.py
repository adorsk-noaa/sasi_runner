from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
import sasi_runner.app.sasi_model_config.util.validation as validation
from sasi_data.util.data_generators import generate_data_dir
import os
import tempfile
import zipfile


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

def generate_config(bundled=True):

    config = SASIModelConfig(id=get_id(), title="tst_config")

    data_dir = generate_data_dir()

    # Bundle style.
    if bundled:
        hndl, archivename = tempfile.mkstemp(prefix="sr_bundle.", suffix=".zip")
        zipdir(data_dir, archivename)
        config.bundle = SASIFile(
            id=get_id(),
            path=archivename,
            filename=os.path.basename(archivename),
            category='config_bundle',
            size=12345,
            created=None
        )

    # Individual file style.
    else:
        target_dir = tempfile.mkdtemp(prefix="ctest.")
        for section in [
            'substrates', 
            'features', 
            'energys', 
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
