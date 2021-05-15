"""Wrapper for remote and local logging"""

import logging
from logging.handlers import WatchedFileHandler
import os
import sys

try:
    from google.cloud.logging.handlers import CloudLoggingHandler
except ImportError:
    pass
from env import DAQ_RUN_DIR

LOGGERS = {}
_DEFAULT_LOG_FILE = os.path.join(DAQ_RUN_DIR, "daq.log")

def set_stackdriver_client(client, labels=None):
    """Sets stackdriver client"""
    stackdriver_client_name, stackdriver_client = client
    stackdriver_handler = CloudLoggingHandler(stackdriver_client,
                                              name=stackdriver_client_name,
                                              labels=labels)
    for name, logger in LOGGERS.items():
        # filters out root logger
        if name:
            logger.addHandler(stackdriver_handler)
    set_stackdriver_client.stackdriver_handler = stackdriver_handler


def _get_file_handler():
    if not _get_file_handler.log_handler:
        log_file_path = os.getenv('DAQ_LOG', _DEFAULT_LOG_FILE)
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        _get_file_handler.log_handler = WatchedFileHandler(log_file_path)
    return _get_file_handler.log_handler


def get_logger(name=None, log_file=None):
    """Gets the named logger"""
    if name not in LOGGERS:
        LOGGERS[name] = logging.getLogger(name)
        if not name:  # Root logger
            LOGGERS[name].addHandler(_get_file_handler())
            LOGGERS[name].addHandler(logging.StreamHandler(sys.stdout))
        if name and set_stackdriver_client.stackdriver_handler:
            LOGGERS[name].addHandler(set_stackdriver_client.stackdriver_handler)

    if log_file:
        return ForkingLogger(LOGGERS[name], log_file)

    return LOGGERS[name]


class ForkingLogger:
    """Simple wrapper class for logging to normal place and a file"""

    def __init__(self, logger, log_file):
        self._logger = logger
        self._log_file = log_file
        os.makedirs(os.path.dirname(log_file))

    def _write(self, prefix, fmt, *args):
        with open(self._log_file, 'a') as output_stream:
            output_stream.write('%s %s\n' % (prefix, fmt % args))

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


def set_config(level='info', fmt=None, datefmt=None):
    """Sets config for all loggers"""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)

set_stackdriver_client.stackdriver_handler = None
_get_file_handler.log_handler = None
