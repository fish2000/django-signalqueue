#/usr/bin/env python
from distutils.core import setup

setup(
    name='django-delegate',
    version='0.1.0',
    description='Automatic delegate methods for Django managers and querysets without runtime dispatch penalties.',
    author='Alexander Bohn',
    author_email='fish2000@gmail.com',
    maintainer='Alexander Bohn',
    maintainer_email='fish2000@gmail.com',
    license='BSD',
    url='http://github.com/fish2000/django-delegate/',
    keywords=[
        'django',
        'delegate',
        'queryset',
        'manager',
    ],
    packages=[
        'delegate',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
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

