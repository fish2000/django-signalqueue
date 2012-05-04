#/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

__author__ = 'Alexander Bohn'
__version__ = (0, 3, 9)

setup(
    name='django-signalqueue',
    version='%s.%s.%s' % __version__,
    description='Truly asynchronous signal dispatch for Django!',
    author=__author__,
    author_email='fish2000@gmail.com',
    maintainer=__author__,
    maintainer_email='fish2000@gmail.com',
    license='BSD',
    url='http://github.com/fish2000/django-signalqueue/',
    keywords=[
        'django',
        'signals',
        'async',
        'asynchronous',
        'queue',
    ],
    packages=[
        'signalqueue',
        'signalqueue.management',
        'signalqueue.management.commands',
        'signalqueue.settings',
        'signalqueue.templatetags',
        'signalqueue.worker',
    ],
    include_package_data=True,
    package_data={
        'signalqueue': [
            'fixtures/*.json',
            'settings/*.conf',
            'static/signalqueue/js/*.js',
            'static/signalqueue/coffee/*.coffee',
            'static/socket.io-client/*',
            'templates/*.html',
            'templates/admin/*.html',
        ],
    },
    install_requires=[
        'django-delegate>=0.2.2', 'tornado', 'tornadio2', 'redis',
    ],
    tests_require=[
        'nose', 'rednose', 'django-nose',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities'
    ]
)

