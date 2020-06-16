"""Unit tests for configurator"""

import unittest
import os
import sys

from daq.configurator import Configurator, print_config

import logging
logger = logging.getLogger()
logger.level = logging.INFO


def dict_to_conf_str(obj):
    """Dump dict as key=value to str object."""
    config_list = []
    for key in sorted(obj.keys()):
        value = obj[key]
        config_list.append("%s=%s" % (key, obj[key]))
    return '\n'.join(config_list)

TEMP_CONF_FILE = 'temp.conf'


class TestConfigurator(unittest.TestCase):
    """Test class for Configurator"""

    config = {
        'monitor_scan_sec' : '30',
        'default_timeout_sec' : '350',
        'base_conf' : 'resources/setups/baseline/module_config.json',
        'site_path' : 'local/site/',
        'initial_dhcp_lease_time' : '120s',
        'dhcp_lease_time' : '500s',
        'long_dhcp_response_sec' : '105'
    }

    def setUp(self):
        tmpfile = open(TEMP_CONF_FILE, 'w+')
        tmpfile.write(dict_to_conf_str(self.config))
        tmpfile.close()

    def tearDown(self):
        os.remove(TEMP_CONF_FILE)

    def test_config_load(self):
        """Test config is loaded properly"""
        configurator = Configurator()
        args = ['test', TEMP_CONF_FILE]
        read_config = configurator.parse_args(args)
        self.assertEqual(self.config, read_config)

if __name__ == '__main__':
    unittest.main()
