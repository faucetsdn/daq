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


def get_interface_name():
    """Get main interface name from test container"""
    return '%s-eth0' % socket.gethostname()


def get_interface_ip(ifname):
    """Get interface IP"""
    _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        _socket.fileno(), 0x8915, struct.pack('256s', bytes(ifname[:15], 'utf-8'))
    )[20:24])


def get_interface_mac(ifname):
    """Get interface MAC"""
    _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    mac_addr = fcntl.ioctl(
        _socket.fileno(), 0x8927,  struct.pack('256s', bytes(ifname, 'utf-8')[:15]))
    formatted_mac = ':'.join('%02x' % b for b in mac_addr[18:24])
    return formatted_mac


class MessageParseError(Exception):
    """Error for when parsing cannot be successfully completed."""
    pass
