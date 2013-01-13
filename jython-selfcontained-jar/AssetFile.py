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
        'type': 'url',
        'source': 'http://pypi.python.org/packages/source/J/Jinja2/Jinja2-2.6.tar.gz',
        'untar': True,
        'path': 'Jinja2-2.6/jinja2',
    },
    'blinker' : {
        'type': 'url',
        'source': 'http://pypi.python.org/packages/source/b/blinker/blinker-1.2.tar.gz',
        'untar': True,
        'path': 'blinker-1.2/blinker',
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
    'sasipedia' : {
        'type': 'git',
        'source': 'https://github.com/adorsk-noaa/sasipedia.git',
        'path': 'lib/sasipedia',
    },
    'sqlalchemy' : {
        'type': 'url',
        'unzip': True,
        'path': 'sqlalchemy-rel_0_8/lib/sqlalchemy',
        'source': 'http://hg.sqlalchemy.org/sqlalchemy/archive/rel_0_8.zip' ,
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
    'sqlalchemy_h2' : {
        'type': 'git',
        'source': 'https://github.com/adorsk/sqlalchemy_h2.git',
        'path': 'sqlalchemy_h2',
    },
    'jython-full.jar' : {
        'type': 'rsync',
        'source': '/home/adorsk/tools/jython/jython-dev/dist/jython-standalone.jar'
    },
    'java-lib' : {
        'type': 'rsync',
        'source': '/home/adorsk/tools/jython/jython-dev/dist/javalib'
    },
    'jenv-java-lib' : {
        'type': 'rsync',
        'source': '/home/adorsk/projects/noaa/jenv/javalib'
    },
    'spring_utilities' : {
        'type': 'url',
        'source': 'https://gist.github.com/raw/4524185/gistfile1.txt'
    }
}
