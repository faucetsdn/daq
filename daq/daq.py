#!/usr/bin/env python

"""Main entrypoint for DAQ. Handles command line parsing and other
misc setup tasks."""

import logging
import os
import sys

from ConfigParser import ConfigParser
from StringIO import StringIO

from mininet import log as minilog

import runner

LOGGER = logging.getLogger('daq')
ALT_LOG = logging.getLogger('mininet')

FLAG_MAP = {
    's': 'single_shot',
    'e': 'event_trigger',
    'l': 'result_linger',
    'd': 'debug_mode',
    'c': 'use_console'
}

def _stripped_alt_logger(self, level, msg, *args, **kwargs):
    #pylint: disable=unused-argument
    """A logger for messages that strips whitespace"""
    stripped = msg.strip()
    if stripped:
        #pylint: disable=protected-access
        ALT_LOG._log(level, stripped, *args, **kwargs)

def _configure_logging(config):
    log_def = 'debug' if config.get('debug_mode') else 'info'
    daq_env = config.get('daq_loglevel', log_def)
    logging.basicConfig(level=minilog.LEVELS.get(daq_env, minilog.LEVELS['info']))

    mininet_env = config.get('mininet_loglevel')
    minilog.setLogLevel(mininet_env if mininet_env else 'info')

    #pylint: disable=protected-access
    minilog.MininetLogger._log = _stripped_alt_logger

def _write_pid_file():
    pid = os.getpid()
    LOGGER.info('DAQ pid is %d', pid)
    with open('inst/daq.pid', 'w') as pid_file:
        pid_file.write(str(pid))

def _read_config_into(filename, config):
    parser = ConfigParser()
    with open(filename) as stream:
        stream = StringIO("[top]\n" + stream.read())
        parser.readfp(stream)
    for item in parser.items('top'):
        config[item[0]] = item[1]

def _parse_args(args):
    config = {}
    for arg in args[1:]:
        if arg:
            if arg[0] == '-':
                if arg[1:] in FLAG_MAP:
                    config[FLAG_MAP[arg[1:]]] = True
                else:
                    raise Exception('Unknown command line arg %s' % arg)
            elif '=' in arg:
                parts = arg.split('=', 1)
                config[parts[0]] = parts[1]
            else:
                _read_config_into(arg, config)
    return config

def _execute():
    config = _parse_args(sys.argv)
    _configure_logging(config)

    _write_pid_file()

    daq_runner = runner.DAQRunner(config)
    daq_runner.initialize()
    daq_runner.main_loop()
    daq_runner.cleanup()

    result = daq_runner.finalize()
    LOGGER.info('DAQ runner returned %d', result)

    return result


if __name__ == '__main__':
    assert os.getuid() == 0, 'Must run DAQ as root.'
    sys.exit(_execute())
