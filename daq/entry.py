#!/usr/bin/env python3

"""Main entry-point for DAQ. Handles command line parsing and other
misc setup tasks."""

import os
import signal
import sys

from mininet import log as minilog
from env import DAQ_RUN_DIR
import logger
import runner
import configurator
import utils

from proto import system_config_pb2 as sys_config

ROOT_LOG = logger.get_logger()
LOGGER = logger.get_logger('daq')
ALT_LOG = logger.get_logger('mininet')

_PID_FILE = os.path.join(DAQ_RUN_DIR, 'daq.pid')
_LOG_FORMAT = "%(asctime)s %(name)-8s %(levelname)-7s %(message)s"
_DATE_FORMAT = '%b %02d %H:%M:%S'

_CONFIG_MIGRATIONS = {
    'sec_port': 'switch_setup.uplink_port',
    'ext_ctrl': 'switch_setup.ctrl_intf',
    'ext_intf': 'switch_setup.data_intf',
    'ext_ofpt': 'switch_setup.lo_port',
    'ext_ofip': 'switch_setup.lo_addr',
    'ext_loip': 'switch_setup.mods_addr',
    'ext_dpid': 'switch_setup.of_dpid',
    'ext_addr': 'switch_setup.ip_addr',
    'switch_model': 'switch_setup.model',
    'switch_username': 'switch_setup.username',
    'switch_password': 'switch_setup.password',
    'startup_cmds': 'interfaces.<iface_name>.opts= (dictionary)',
    'intf_names': 'interfaces.<iface_name>.opts= (dictionary)'
}

class DAQ:
    """Wrapper class for configuration management"""

    def __init__(self, args):
        config_helper = configurator.Configurator(raw_print=True)
        self.config = config_helper.parse_args(args)

    def validate_config(self):
        """Validate DAQ configuration"""
        errors = False
        for old_key in _CONFIG_MIGRATIONS:
            if old_key in self.config:
                errors = True
                LOGGER.warning("Config '%s' is now '%s'",
                               old_key, _CONFIG_MIGRATIONS[old_key])
        if errors:
            LOGGER.error('Old style configs found. Goodby.')
            return False

        # Work around int/str ambiguity, force to base-10 string
        of_dpid = self.config.get('switch_setup', {}).get('of_dpid')
        if of_dpid:
            self.config.get('switch_setup', {})['of_dpid'] = str(int(str(of_dpid), 0))

        # Validate structure of config by reading it into a pb message.
        utils.dict_proto(self.config, sys_config.DaqConfig)

        return True

    def configure_logging(self):
        """Configure logging"""
        config = self.config
        log_def = 'debug' if config.get('debug_mode') else 'info'
        daq_env = config.get('daq_loglevel', log_def)
        level = minilog.LEVELS.get(daq_env, minilog.LEVELS['info'])

        logger.set_config(level=level, format=_LOG_FORMAT, datefmt=_DATE_FORMAT)

        # For some reason this is necessary for travis.ci
        ROOT_LOG.setLevel(level)

        # This handler is used by everything, so be permissive here.
        ROOT_LOG.handlers[0].setLevel(minilog.LEVELS['debug'])

        mininet_env = config.get('mininet_loglevel', 'info')
        minilog.setLogLevel(mininet_env)

        # pylint: disable=protected-access
        minilog.MininetLogger._log = _stripped_alt_logger


def _stripped_alt_logger(self, level, msg, *args, **kwargs):
    # pylint: disable=unused-argument
    """A logger for messages that strips whitespace"""
    stripped = msg.strip()
    if stripped:
        # pylint: disable=protected-access
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

    if not daq.validate_config():
        return 1

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
