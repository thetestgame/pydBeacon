"""
Copyright (c) Jordan Maxwell, All Rights Reserved.
See LICENSE file in the project root for full license information.
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from pathlib import Path
repository_directory = Path(__file__).parent
long_description = (repository_directory / "README.md").read_text()

setup(
    name='pydBeacon',
    description="An open source Python library for reading/writing Disney Theme Park Bluetooth Beacon data.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    version='1.0.0',
    author='Jordan Maxwell',
    maintainer='Jordan Maxwell',
    url='https://github.com/thetestgame/pydBeacon',
    packages=['dbeacon'],
    classifiers=[
        'Programming Language :: Python :: 3',
    ])