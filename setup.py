#!/usr/bin/env python

from glob import glob
from setuptools import setup

setup(
    name = "diy-lsi",
    version = "0.1",
    author = "Narayan Desai",
    author_email = "narayan.desai+lsi@gmail.com",
    description = ("Tools for managing lsi disk arrays on illumos"),
    license = "BSD",
    keywords = "LSI Illumos",
    url = "https://github.com/narayandesai/diy-lsi",
    packages=['diylsi'],
    scripts = glob('tools/*'),
    long_description=open('README.md').read(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
