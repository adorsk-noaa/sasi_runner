from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
import sasi_runner.app.sasi_model_config.util.validation as validation
import os


base_dir = os.path.dirname(os.path.abspath(__file__))
base_data_dir = os.path.join(base_dir, "test_data")

id_= 0
def get_id():
    global id_
    id_ += 1
    return id_

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
