from sasi_runner.config import config as sr_conf
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker, class_mapper, aliased
from sqlalchemy.orm.properties import RelationshipProperty


engine = create_engine(sr_conf['DB_URI'], convert_unicode=True)
metadata = MetaData()
session = scoped_session(sessionmaker(bind=engine))

def init_db(bind=engine):
    metadata.create_all(bind=bind)

def clear_db(bind=engine):
	metadata.drop_all(bind=bind)

def get_attr_target_class(clazz, attr):
    """
    Helper function to get a mapped attribute's 
    target class.
    """
    target_class = None
    prop = class_mapper(clazz).get_property(attr)
    if isinstance(prop, RelationshipProperty):
        target_class = prop.mapper.class_
    return target_class
