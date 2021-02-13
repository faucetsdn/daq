#!/usr/bin/env python3

from __future__ import absolute_import
import setuptools
import shutil
import os
import tempfile


def get_files_mapping_env():
    with open('debian/FILES_MAPPING') as f:
        return f.read().split('\n')


def get_version():
    return os.popen('git describe').read().strip()


def build_entry_script(tmp):
    with open(os.path.join(tmp, 'daq'), 'w') as f:
        script = """#!/bin/bash
if [ "$EUID" -ne 0 ]; then
    echo Please run DAQ as root
    exit
fi
%s
export DAQ_VERSION="%s"
LSB_RAW=$(lsb_release -a)
export DAQ_LSB_RELEASE=$(echo $LSB_RAW)
export DAQ_SYS_UNAME=$(uname -a)

export DAQ_DIR=`python3 -c 'import daq; import os; print(os.path.dirname(daq.__file__))'`
source $DAQ_LIB/bin/config_base.sh
python3 $DAQ_DIR/daq.py $conf_file $@
        """ % (";".join(get_files_mapping_env()), get_version())
        f.write(script)
    return os.path.join(tmp, 'daq')


def build_data_files(prefix, package_prefix):
    paths = []
    for root, dirs, files in os.walk(prefix):
        if files:
            paths.append((os.path.join(package_prefix, root[len(prefix) + 1:]),
                         [os.path.join(root, name) for name in files]))
    return paths


def build_source_files(tmp):
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree('daq', tmp, symlinks=True)
    shutil.copytree('libs/proto', os.path.join(tmp, 'proto'), symlinks=True)
    shutil.copytree('faucet/clib', os.path.join(tmp, 'clib'), symlinks=True)
    return tmp


dirs = os.listdir('.')
assert all([repo in dirs for repo in ('faucet',)]), \
    'Missing dependent repos. Please run bin/setup_dev'

with tempfile.TemporaryDirectory(dir='.') as tmp:
    setuptools.setup(
        package_dir={
            'daq': build_source_files(tmp)
        },
        package_data={'daq': ['proto/*', 'clib/*', 'forch/proto/*']},
        setup_requires=['pbr>=1.9', 'setuptools>=17.1'],
        pbr=True,
        scripts=[
            build_entry_script(tmp),
        ],
        data_files=[
            *build_data_files('bin', 'lib/daq/bin'),
            *build_data_files('cmd', 'lib/daq/cmd'),
            *build_data_files('resources/setups', 'lib/daq/resources/setups'),
            *build_data_files('subset', 'lib/daq/subset'),
            *build_data_files('usi', 'lib/daq/usi'),
            *build_data_files('config/modules', 'lib/daq/config/modules'),
            *build_data_files('config/system', 'lib/daq/config/system'),
        ]
    )
