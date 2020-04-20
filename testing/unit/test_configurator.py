"""Unit tests for configurator"""

import unittest
import os

from daq.configurator import Configurator, print_config

def dict_to_str(obj):
    """Dump dict as key=value to str object."""
    config_list = []
    for key in sorted(obj.keys()):
        value = obj[key]
        quote = '"' if ' ' in str(value) else ''
        config_list.append("%s=%s" % (key, obj[key]))
    return '\n'.join(config_list)


class TestConfigurator(unittest.TestCase):
    """Test class for Configurator"""

    config = {
        'monitor_scan_sec' : '30',
        'default_timeout_sec' : '350',
        'base_conf' : 'misc/module_config.json',
        'site_path' : 'local/site/',
        'initial_dhcp_lease_time' : '120s',
        'dhcp_lease_time' : '500s',
        'long_dhcp_response_sec' : '105'
    }

    def setUp(self):
        tmpfile = open('temp.conf', 'w+')
        tmpfile.write(dict_to_str(self.config))
        tmpfile.close()

    def tearDown(self):
        os.remove('temp.conf')

    def test_config_load(self):
        """Test config is loaded properly"""
        configurator = Configurator()
        args = ['test', 'temp.conf']
        read_config = configurator.parse_args(args)
        self.assertEqual(self.config, read_config)

if __name__ == '__main__':
    unittest.main()
