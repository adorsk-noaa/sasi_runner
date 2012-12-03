config = {
    'CACHE_DIR': 'cache',
    'TARGET_DIR': 'assets'
}

assets = {
    'setuptools.egg' : {
        'type': 'url',
        'source': 'http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg'
    },
    'jinja2' : {
        'type': 'rsync',
        'source': '/home/adorsk/projects/sasi_runner/jy2.7/Lib/site-packages/jinja2',
    },
    'blinker' : {
        'type': 'rsync',
        'source': '/home/adorsk/projects/sasi_runner/jy2.7/Lib/site-packages/blinker',
    },
    'sa_dao' : {
        'type': 'git',
        'source': 'https://github.com/adorsk-noaa/sqlalchemy_dao.git',
        'path': 'lib/sa_dao',
    },
    'sasi_data' : {
        'type': 'git',
        'source': 'https://github.com/adorsk-noaa/sasi_data',
        'path': 'lib/sasi_data',
    },
    'sasi_model' : {
        'type': 'git',
        'source': 'https://github.com/adorsk-noaa/sasi_model',
        'path': 'lib/sasi_model',
    },
    'sasipedia' : {
        'type': 'git',
        'source': 'https://github.com/adorsk-noaa/sasipedia.git',
        'path': 'lib/sasipedia',
    },
    'sqlalchemy' : {
        'type': 'hg',
        'source': 'https://adorsk@bitbucket.org/adorsk/sqlalchemy',
        'path': 'lib/sqlalchemy',
    },
    'geoalchemy': {
        'type': 'git',
        'source': 'https://github.com/adorsk/geoalchemy.git',
        'path': 'geoalchemy',
    },
    'sasi_runner' : {
        'type': 'git',
        'source': 'https://github.com/adorsk-noaa/sasi_runner',
        'path': 'lib/sasi_runner',
    },
    'task_manager' : {
        'type': 'git',
        'source': 'https://github.com/adorsk/TaskManager.git',
        'path': 'lib/task_manager',
    },
    'jython-full.jar' : {
        'type': 'rsync',
        'source': '/home/adorsk/tools/jython/jython-dev/dist/jython-standalone.jar'
    },
    'java-lib' : {
        'type': 'rsync',
        'source': '/home/adorsk/tools/jython/jython-dev/dist/javalib'
    },
}
