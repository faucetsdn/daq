"""Utility Functions"""
import logging
import random
import sys
from collections import namedtuple  # pytype: disable=pyi-error


def get_logger(logname):
    """Create and return a logger object."""
    logger = logging.getLogger(logname)
    logger.setLevel(logging.INFO)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(stdout_handler)
    return logger


class MessageParseError(Exception):
    """Error for when parsing cannot be successfully completed."""
    pass
