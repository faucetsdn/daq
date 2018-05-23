#!/usr/bin/env python

"""Device Automated Qualification testing framework"""

import logging
import os
import sys

from ConfigParser import ConfigParser
from StringIO import StringIO

from mininet import log as minilog
from mininet.log import LEVELS, MininetLogger

from runner import DAQRunner

LOGGER = logging.getLogger('daq')
ALT_LOG = logging.getLogger('mininet')

def _stripped_alt_logger(_self, level, msg, *args, **kwargs):
    """A logger for messages that strips whitespace"""
    stripped = msg.strip()
    if stripped:
        #pylint: disable-msg=protected-access
        ALT_LOG._log(level, stripped, *args, **kwargs)

def _configure_logging(config):
    daq_env = config.get('daq_loglevel')
    logging.basicConfig(level=LEVELS.get(daq_env, LEVELS['info']))

    mininet_env = config.get('mininet_loglevel')
    minilog.setLogLevel(mininet_env if mininet_env else 'info')

    #pylint: disable-msg=protected-access
    MininetLogger._log = _stripped_alt_logger

def _write_pid_file():
    pid = os.getpid()
    LOGGER.info('DAQ pid is %d', pid)
    with open('inst/daq.pid', 'w') as file:
        file.write(str(pid))

def _read_config_into(filename, config):
    parser = ConfigParser()
    with open(filename) as stream:
        stream = StringIO("[top]\n" + stream.read())
        parser.readfp(stream)
    for item in parser.items('top'):
        config[item[0]] = item[1]

def _parse_args(args):
    config = {}
    first = True
    for arg in args:
        if first:
            first = False
        elif arg[0] == '-':
            config[arg[1:]] = True
        elif '=' in arg:
            parts = arg.split('=', 1)
            config[parts[0]] = parts[1]
        else:
            _read_config_into(arg, config)
    return config


if __name__ == '__main__':
    assert os.getuid() == 0, 'Must run DAQ as root.'

    CONFIG = _parse_args(sys.argv)
    _configure_logging(CONFIG)

    _write_pid_file()

    RUNNER = DAQRunner(CONFIG)
    RUNNER.initialize()
    RUNNER.main_loop()
    RUNNER.cleanup()
    return_code = RUNNER.finalize()

    LOGGER.info('Exiting with return code %s', return_code)
    sys.exit(return_code)
