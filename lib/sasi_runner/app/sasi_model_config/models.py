from sasi_runner.app import db 
from sasi_runner.app.sasi_file.models import SASIFile
from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import mapper, relationship, backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.associationproxy import association_proxy


class SASIModelConfig(object):

    # '_fileds_dict' will be populated by mapping of SASIMOdelConfig_SASI_FILE.
    files = association_proxy(
        '_files_dict', 'file', creator=lambda k, v: SASIModelConfig_SASIFile(k, v)
    )

    def __init__(self, id=None, title="New Configuration"): 
        self.id = id
        self.title = title

    def clone(self):
        """
        Clone a config, w/out cloning its id.
        """
        clone = SASIModelConfig()
        clone.title = self.title
        if self.files:
            clone.files = self.files.copy()
        return clone

class SASIModelConfig_SASIFile(object):
    """ Association class. """
    def __init__(self, file_type=None, file_=None, config=None):
        self.file_type = file_type
        self.file = file_
        self.config = config

configs_table = Table('sasi_model_config', db.metadata,
              Column('id', Integer, primary_key=True),
              Column('title', String),
             )

configs_files_table = Table(
    'sasi_model_config__sasi_file', db.metadata,
    Column('config_id', Integer, ForeignKey('sasi_model_config.id'), primary_key=True),
    Column('file_id', Integer, ForeignKey('sasi_file.id'), primary_key=True),
    Column('file_type', String, primary_key=True),
)

mapper(SASIModelConfig, configs_table)
mapper(
    SASIModelConfig_SASIFile, configs_files_table, 
    properties={
        'config': relationship(
            SASIModelConfig,
            backref=backref(
                '_files_dict', 
                cascade="all, delete-orphan",
                collection_class=attribute_mapped_collection('file_type'),
            )
        ),
        'file': relationship(
            SASIFile, 
            backref=backref('_configs', cascade="all, delete-orphan")
        ),
    }
)
