#!/usr/bin/env python3

"""Main entrypoint for DAQ. Handles command line parsing and other
misc setup tasks."""

import logging
import os
import re
import signal
import sys

from mininet import log as minilog

import runner

ROOTLOG = logging.getLogger()
LOGGER = logging.getLogger('daq')
ALT_LOG = logging.getLogger('mininet')

_PID_FILE = 'inst/daq.pid'

FLAG_MAP = {
    'c': 'use_console',
    'd': 'debug_mode',
    'e': 'event_trigger',
    'f': 'fail_mode',
    'h': 'show_help',
    'l': 'result_linger',
    'n': 'no_test',
    's': 'single_shot'
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
    level = minilog.LEVELS.get(daq_env, minilog.LEVELS['info'])

    logging.basicConfig(level=level)

    # For some reason this is necessary for travis.ci
    ROOTLOG.setLevel(level)

    # This handler is used by everything, so be permissive here.
    ROOTLOG.handlers[0].setLevel(minilog.LEVELS['debug'])

    mininet_env = config.get('mininet_loglevel', 'info')
    minilog.setLogLevel(mininet_env)

    #pylint: disable=protected-access
    minilog.MininetLogger._log = _stripped_alt_logger

def _write_pid_file():
    pid = os.getpid()
    LOGGER.info('pid is %d', pid)
    with open(_PID_FILE, 'w') as pid_file:
        pid_file.write(str(pid))

def _read_config_into(filename, config):
    print('Reading config from %s' % filename)
    with open(filename) as file:
        line = file.readline()
        while line:
            parts = re.sub(r'#.*', '', line).strip().split('=')
            entry = parts[0].split() if parts else None
            if len(parts) == 2:
                config[parts[0].strip()] = parts[1].strip().strip('"').strip("'")
            elif len(entry) == 2 and entry[0] == 'source':
                _read_config_into(entry[1], config)
            elif parts and parts[0]:
                raise Exception('Unknown config entry: %s' % line)
            line = file.readline()

def _parse_args(args):
    config = {}
    for arg in args[1:]:
        if arg:
            print('processing arg: %s' % arg)
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

def _show_help():
    print("Common run options:")
    for option in FLAG_MAP:
        print("  -%s: %s" % (option, FLAG_MAP[option]))
    print("See system.conf for a detailed accounting of potential options.")

def _execute():
    config = _parse_args(sys.argv)
    _configure_logging(config)
    LOGGER.info('configuration map: %s', config)

    if 'show_help' in config:
        _show_help()
        return 0

    _write_pid_file()

    signal.signal(signal.SIGINT, signal.default_int_handler)
    signal.signal(signal.SIGTERM, signal.default_int_handler)

    daq_runner = runner.DAQRunner(config)
    daq_runner.initialize()
    daq_runner.main_loop()
    daq_runner.cleanup()

    result = daq_runner.finalize()
    LOGGER.info('DAQ runner returned %d', result)

    os.remove(_PID_FILE)

    return result


if __name__ == '__main__':
    assert os.getuid() == 0, 'Must run DAQ as root.'
    sys.exit(_execute())
