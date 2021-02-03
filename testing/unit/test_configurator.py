"""Unit tests for configurator"""

import unittest
from unittest.mock import patch
import logging
import os
import yaml

from daq.configurator import Configurator, print_config

LOGGER = logging.getLogger()
LOGGER.level = logging.INFO


def dict_to_conf_str(obj):
    """Dump dict as key=value to str object."""
    config_list = []
    for key in sorted(obj.keys()):
        value = obj[key]
        config_list.append("%s=%s" % (key, value))
    return '\n'.join(config_list)

TEMP_CONF_FILE = 'temp.conf'
TEMP_WITH_INCLUDE = 'temp_with_include.yaml'
TEMP_WITH_DEEP_INCLUDE = 'temp_with_deep_include.yaml'
TEMP_WITH_CIRCULAR_INCLUDE = 'temp_with_circular_include.yaml'
TEMP_WITH_CIRCULAR_INCLUDE2 = 'temp_with_circular_include2.yaml'

class TestConfigurator(unittest.TestCase):
    """Test class for Configurator"""

    config_files = {
        TEMP_CONF_FILE: {
            'monitor_scan_sec': '30',
            'default_timeout_sec': '350',
            'base_conf': 'resources/setups/baseline/base_config.json',
            'site_path': 'local/site/',
            'initial_dhcp_lease_time': '120s',
            'dhcp_lease_time': '500s',
            'long_dhcp_response_sec': '105'
        },
        TEMP_WITH_INCLUDE: {
            'include': TEMP_CONF_FILE,
            'dhcp_lease_time': '0',
            'dict': {
                'k1': {
                    'k2': 0,
                },
                'k2': 2
            }
        },
        TEMP_WITH_DEEP_INCLUDE: {
            'include': TEMP_WITH_INCLUDE,
            'dhcp_lease_time': '1s',
            'dict': {
                'k1': {
                    'k1': 1,
                    'k2': 2
                }
            }
        },
        TEMP_WITH_CIRCULAR_INCLUDE: {
            'include': TEMP_WITH_CIRCULAR_INCLUDE2
        },
        TEMP_WITH_CIRCULAR_INCLUDE2: {
            'include': TEMP_WITH_CIRCULAR_INCLUDE
        },
    }

    def setUp(self):
        for file_path, config in self.config_files.items():
            with open(file_path, 'w+') as tempfile:
                if file_path.endswith('.conf'):
                    tempfile.write(dict_to_conf_str(config))
                elif file_path.endswith('.yaml'):
                    yaml.dump(config, tempfile)

    def tearDown(self):
        for file_path in self.config_files:
            os.remove(file_path)

    def test_config_load(self):
        """Test config is loaded properly"""
        configurator = Configurator()
        args = ['test', TEMP_CONF_FILE]
        read_config = configurator.parse_args(args)
        self.assertEqual(self.config_files[TEMP_CONF_FILE], read_config)

    def test_config_with_basic_include(self):
        """Basic include file test"""
        configurator = Configurator()
        args = ['test', TEMP_WITH_INCLUDE]
        read_config = configurator.parse_args(args)
        self.assertEqual({
            'monitor_scan_sec': '30',
            'default_timeout_sec': '350',
            'base_conf': 'resources/setups/baseline/base_config.json',
            'site_path': 'local/site/',
            'initial_dhcp_lease_time': '120s',
            'long_dhcp_response_sec': '105',
            'dhcp_lease_time': '0',
            'dict': {
                'k1': {
                    'k2': 0,
                },
                'k2': 2
            }
        }, read_config)

    def test_config_with_deep_include(self):
        """Deep include test"""
        configurator = Configurator()
        args = ['test', TEMP_WITH_DEEP_INCLUDE]
        read_config = configurator.parse_args(args)
        self.assertEqual({
            'monitor_scan_sec': '30',
            'default_timeout_sec': '350',
            'base_conf': 'resources/setups/baseline/base_config.json',
            'site_path': 'local/site/',
            'initial_dhcp_lease_time': '120s',
            'long_dhcp_response_sec': '105',
            'dhcp_lease_time': '1s',
            'dict': {
                'k1': {
                    'k1': 1,
                    'k2': 2
                },
                'k2': 2
            }
        }, read_config)

    def test_config_override(self):
        """Overriding config test"""
        configurator = Configurator()
        args = ['test', TEMP_WITH_INCLUDE, 'initial_dhcp_lease_time=999s', 'dhcp_lease_time=999']
        read_config = configurator.parse_args(args)
        self.assertEqual({
            'monitor_scan_sec': '30',
            'default_timeout_sec': '350',
            'base_conf': 'resources/setups/baseline/base_config.json',
            'site_path': 'local/site/',
            'initial_dhcp_lease_time': '999s',
            'long_dhcp_response_sec': '105',
            'dhcp_lease_time': '999',
            'dict': {
                'k1': {
                    'k2': 0,
                },
                'k2': 2
            }
        }, read_config)

    def test_circular_include_in_config(self):
        """Circular include test"""
        configurator = Configurator()
        args = ['test', TEMP_WITH_CIRCULAR_INCLUDE]
        with self.assertRaises(Exception):
            configurator.parse_args(args)

    @patch('builtins.print')
    def test_print_config(self, mock_print):
        """Test the print config capability"""
        configurator = Configurator()
        args = ['test', TEMP_WITH_INCLUDE]
        print_config(configurator.parse_args(args))
        mock_print.assert_called_with(
            'base_conf=resources/setups/baseline/base_config.json',
            'default_timeout_sec=350',
            'dhcp_lease_time=0',
            'dict.k1.k2=0',
            'dict.k2=2',
            'initial_dhcp_lease_time=120s',
            'long_dhcp_response_sec=105',
            'monitor_scan_sec=30',
            'site_path=local/site/', sep='\n')


if __name__ == '__main__':
    unittest.main()
