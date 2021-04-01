"""Utility Functions"""
from __future__ import absolute_import
import logging
import fcntl
import socket
import struct
import sys


def get_logger(logname):
    """Create and return a logger object."""
    logger = logging.getLogger(logname)
    logger.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(stdout_handler)

    logfile_handler = logging.FileHandler('/tmp/dot1x_debug_log')
    logfile_handler.setLevel(logging.DEBUG)
    logfile_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(logfile_handler)

    return logger


def get_interface_name():
    """Get main interface name from test container"""
    return '%s-eth0' % socket.gethostname()


def get_interface_ip(ifname, _socket):
    """Get interface IP"""
    return socket.inet_ntoa(fcntl.ioctl(
        _socket.fileno(), 0x8915, struct.pack('256s', bytes(ifname[:15], 'utf-8'))
    )[20:24])


class MessageParseError(Exception):
    """Error for when parsing cannot be successfully completed."""
    pass
