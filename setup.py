#/usr/bin/env python
from distutils.core import setup

setup(
    name='django-signalqueue',
    version='0.1.2',
    description='Asynchronous signals for Django.',
    author='Alexander Bohn',
    author_email='fish2000@gmail.com',
    maintainer='Alexander Bohn',
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
    package_data={
        'signalqueue': [
            'fixtures/*.json',
            'static/signalqueue/js/*.js',
            'templates/admin/*.html',
            'templates/queueserver/*.html',
        ],
    },
    install_requires=[
        'django-delegate', 'tornado',
    ],
    test_requires=[
        'nose', 'django-nose',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities'
    ]
)

