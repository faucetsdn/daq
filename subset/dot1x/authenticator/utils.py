"""Utility Functions"""
from __future__ import absolute_import
import logging
import sys


def get_logger(logname):
    """Create and return a logger object."""
    logger = logging.getLogger(logname)
    logger.setLevel(logging.INFO)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(stdout_handler)

    logfile_handler = logging.FileHandler('/tmp/dot1x_debug_log')
    logfile_handler.setLevel(logging.DEBUG)
    logfile_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(logfile_handler)

    return logger


class MessageParseError(Exception):
    """Error for when parsing cannot be successfully completed."""
    pass
