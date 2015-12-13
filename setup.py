#!/usr/bin/env python
# -*- coding: utf-8 -*-

from io import open
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

VERSION_FILE = 'tp/_version.py'

if sys.argv[-1] == 'publish':
    os.system('make release')
    sys.exit()

def open_file(filename):
    """Open and read the file *filename*."""
    with open(filename, encoding='utf-8') as f:
        return f.read()

readme = open_file('README.rst')
history = open_file('HISTORY.rst').replace('.. :changelog:', '')
exec(open_file(VERSION_FILE))

setup(
    name='tpcli',
    version=__version__,
    description='TP is a command-line interface for Targetprocess.',
    long_description=readme + '\n\n' + history,
    author='Thomas Roten',
    author_email='thomas@roten.us',
    url='https://github.com/tsroten/tp',
    packages=[
        'tp',
        'tp.commands',
    ],
    package_dir={'tp': 'tp'},
    include_package_data=True,
    install_requires=[
        'Click >= 5.1',
        'html2text',
        'pyperclip',
        'requests',
        'tabulate',
        'xmltodict',
    ],
    entry_points={
        'console_scripts': ['tp = tp.cli:main'],
        },
    license='MIT',
    keywords='tp,targetprocess,agile,kanban,project,management,cli',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tp.tests',
)
