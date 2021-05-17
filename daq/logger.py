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
_LOG_FORMAT = "%(asctime)s %(name)-8s %(levelname)-7s %(message)s"
_DATE_FORMAT = '%b %02d %H:%M:%S'
_FORMATTER = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

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


def _add_file_handler(logger, log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    log_handler = WatchedFileHandler(log_file)
    log_handler.setFormatter(_FORMATTER)
    logger.addHandler(log_handler)
    return logger


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
        _add_file_handler(LOGGERS[name], log_file)

    return LOGGERS[name]


def set_config(fmt=None, level='info'):
    """Sets config for all loggers"""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    formatter = _FORMATTER if not fmt else (
        logging.Formatter(fmt=fmt, datefmt=_DATE_FORMAT))
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)

set_stackdriver_client.stackdriver_handler = None
_get_file_handler.log_handler = None
