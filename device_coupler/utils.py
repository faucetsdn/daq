"""Utility Functions"""
from __future__ import absolute_import

from google.protobuf import json_format

import logging
import sys
import yaml


def get_logger(logname):
    """Create and return a logger object."""
    logger = logging.getLogger(logname)
    logger.setLevel(logging.INFO)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(stdout_handler)

    logfile_handler = logging.FileHandler('/tmp/device_coupler_log')
    logfile_handler.setLevel(logging.INFO)
    logfile_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(logfile_handler)

    return logger


def enable_debug_logs(logger):
    """Enable debug logs for logger"""
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)


def yaml_proto(file_name, proto_func):
    """Load a yaml file into a proto object"""
    with open(file_name) as stream:
        file_dict = yaml.safe_load(stream)
    return json_format.ParseDict(file_dict, proto_func())


def write_yaml_file(filename, data):
    """Writes dict into a yaml file"""
    directory = os.path.dirname(filename)
    os.makedirs(directory, exist_ok=True)
    with open(filename, "w") as file_stream:
        yaml.safe_dump(data, stream=file_stream)
