config = {
    'CACHE_DIR': 'cache',
    'TARGET_DIR': 'assets'
}

assets = {
    'sa_dao' : {
        'type': 'git',
        'source': 'https://github.com/adorsk-noaa/sqlalchemy_dao.git',
    },
    'sasi_data' : {
        'type': 'git',
        'source': 'https://github.com/adorsk-noaa/sasi_data',
    },
    'sasipedia' : {
        'type': 'git',
        'source': 'https://github.com/adorsk-noaa/sasipedia.git',
    },
    'sqlalchemy' : {
        'type': 'hg',
        'source': 'https://adorsk@bitbucket.org/adorsk/sqlalchemy',
    },
    'geoalchemy': {
        'type': 'git',
        'source': 'https://github.com/adorsk/geoalchemy.git',
    },
}
