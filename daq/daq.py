#!/usr/bin/env python3

"""Main entrypoint for DAQ. Handles command line parsing and other
misc setup tasks."""

import logging
import os
import signal
import sys

from mininet import log as minilog

import runner
import configurator

ROOTLOG = logging.getLogger()
LOGGER = logging.getLogger('daq')
ALT_LOG = logging.getLogger('mininet')

_PID_FILE = 'inst/daq.pid'

class DAQ:
    """Wrapper class for configuration management"""

    def __init__(self, args):
        config_helper = configurator.Configurator(verbose=True)
        self.config = config_helper.parse_args(args)

    def configure_logging(self):
        """Configure logging"""
        config = self.config
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


def _stripped_alt_logger(self, level, msg, *args, **kwargs):
    #pylint: disable=unused-argument
    """A logger for messages that strips whitespace"""
    stripped = msg.strip()
    if stripped:
        #pylint: disable=protected-access
        ALT_LOG._log(level, stripped, *args, **kwargs)

def _write_pid_file():
    pid = os.getpid()
    LOGGER.info('pid is %d', pid)
    with open(_PID_FILE, 'w') as pid_file:
        pid_file.write(str(pid))

def _execute():
    daq = DAQ(sys.argv)
    configurator.print_config(daq.config)
    daq.configure_logging()
    config = daq.config

    if config.get('show_help'):
        configurator.show_help()
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
