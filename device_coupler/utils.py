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
