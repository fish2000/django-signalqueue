#/usr/bin/env python
# encoding: utf-8
"""
setup.py

Created by FI$H 2000 on 2012-06-19.
Copyright (c) 2012 Objects In Space And Time, LLC. All rights reserved.

"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from distributors.dist import SQDistribution
from distributors.clean import really_clean
from distributors.coffeescript import build_coffeescript
from distributors.coffeescript import download_js_libs
from distributors.coffeescript import uglify
from distributors import build_js

__author__ = 'Alexander Bohn'
__version__ = (0, 4, 7)

import os

def get_coffeescript_files():
    out = []
    pattern = '.coffee'
    for root, dirs, files in os.walk(os.path.join(
        'signalqueue', 'static', 'signalqueue', 'coffee')):
        for f in files:
            if f.endswith(pattern):
                out.append(os.path.join(root, f))
    return out

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
    keywords=['django','signals','async','asynchronous','queue'],
    
    distclass=SQDistribution,
    js_package='signalqueue',
    cs_files=get_coffeescript_files(),
    js_libs=[
        'https://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.js',
        'http://cdn.socket.io/stable/socket.io.js'],
    js_outdirs={
        'signalqueue': os.path.join('static', 'signalqueue', 'js') },
    
    cmdclass={
        'build_js': build_js,
        'clean': really_clean,
        
        'build_coffeescript': build_coffeescript,
        'download_js_libs': download_js_libs,
        'uglify': uglify },
    
    entry_points={
        'console_scripts': ['signalqueue-test = signalqueue.testrunner:main'] },
    
    include_package_data=True,
    package_data={
        'signalqueue': [
            'fixtures/*.json',
            'settings/*.conf',
            'static/signalqueue/js/*.js',
            'static/signalqueue/coffee/*.coffee',
            'static/socket.io-client/*',
            'templates/*.html',
            'templates/admin/*.html']},
    
    packages=[
        'distributors',
        'distributors.urlobject',
        'signalqueue',
        'signalqueue.management',
        'signalqueue.management.commands',
        'signalqueue.settings',
        'signalqueue.templatetags',
        'signalqueue.worker'],
    
    setup_requires=[
        'django'],
    
    install_requires=[
        'django-delegate>=0.2.2',
        'tornado', 'tornadio2',
        'redis', 'requests',
        'setproctitle'],
    
    tests_require=[
        'nose', 'rednose', 'django-nose'],
    
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities'])

