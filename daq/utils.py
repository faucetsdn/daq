"""Utility functions for DAQ"""

from __future__ import absolute_import

import os
from google.protobuf import json_format
import yaml

import logger


def yaml_proto(file_name, proto_func):
    """Load a yaml file into a proto object"""
    with open(file_name) as stream:
        file_dict = yaml.safe_load(stream)
    return json_format.ParseDict(file_dict, proto_func())


def proto_dict(message,
               including_default_value_fields=False,
               preserving_proto_field_name=True):
    """Convert a proto message to a standard dict object"""
    return json_format.MessageToDict(
        message,
        including_default_value_fields=including_default_value_fields,
        preserving_proto_field_name=preserving_proto_field_name
    )


def proto_json(message):
    """Convert a proto message to a json string"""
    return json_format.MessageToJson(
        message,
        including_default_value_fields=True,
        preserving_proto_field_name=True,
    )


def dict_proto(message, proto_func, ignore_unknown_fields=False):
    """Convert a standard dict object to a proto object"""
    return json_format.ParseDict(message, proto_func(), ignore_unknown_fields)


def write_pid_file(pid_file, out_logger=None):
    """Write the PID of current process to file"""
    pid = os.getpid()
    if out_logger:
        out_logger.info('Writing pid %d to file %s', pid, pid_file)
    with open(pid_file, 'w') as file:
        file.write(str(pid))


class ForkingLogger:
    """Simple wrapper class for logging to normal place and a file"""

    def __init__(self, prefix, log_file):
        self._prefix = prefix
        self._logger = logger.get_logger('ipaddr')
        self._log_file = log_file
        os.makedirs(os.path.dirname(log_file))

    def _write(self, prefix, fmt, *args):
        with open(self._log_file, 'a') as output_stream:
            output_stream.write('%s %s %s\n' % (self._prefix, prefix, fmt % args))

    def debug(self, *args):
        """Debug"""
        self._logger.debug(*args)
        self._write('DEBUG', *args)

    def info(self, *args):
        """Info log"""
        self._logger.info(*args)
        self._write('INFO ', *args)

    def warning(self, *args):
        """Warning log"""
        self._logger.warning(*args)
        self._write('WARN ', *args)

    def error(self, *args):
        """Error log"""
        self._logger.error(*args)
        self._write('ERROR', *args)
