"""Unit tests for configurator"""

import unittest
import os

#from daq.configurator import Configurator


class TestConfigurator(unittest.TestCase):
    """Test class for Configurator"""

    config_str = '\
    monitor_scan_sec=30\n\
    default_timeout_sec=350\n\
    base_conf=misc/module_config.json\n\
    site_path=local/site/\n\
    initial_dhcp_lease_time=120s\n\
    dhcp_lease_time=500s\n\
    long_dhcp_response_sec=105'

    def setUp(self):
        tmpfile = open('temp.conf', 'w+')
        tmpfile.write(self.config_str)
        tmpfile.close()

    def tearDown(self):
        os.remove('temp.conf')

    def test_config_load(self):
        """Test config is loaded properly"""
        tmpfile = open('temp.conf', 'r')
        print(tmpfile.read())
        tmpfile.close()

if __name__ == '__main__':
    unittest.main()
