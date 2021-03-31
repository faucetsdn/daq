"""Unit tests for AclStateCollector"""

from __future__ import absolute_import

import shutil
import tempfile
import unittest

from acl_state_collector import AclStateCollector

from faucet import config_parser


class MockSample:
    """Mocking the metric samples"""
    def __init__(self, labels, value):
        self.labels = labels
        self.value = value


class AclStateCollectorTestBase(unittest.TestCase):
    """Base setup for AclStateCollector tests"""

    FAUCET_CONFIG = ''
    ACL_SAMPLES = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._temp_dir = None
        self._acl_collector = None

    def setUp(self):
        """Setup fixture for each test method"""
        self._temp_dir = tempfile.mkdtemp()
        _, temp_faucet_config_file = tempfile.mkstemp(dir=self._temp_dir)

        with open(temp_faucet_config_file, 'w') as file:
            file.write(self.FAUCET_CONFIG)
        _, _, dps_config, _ = config_parser.dp_parser(temp_faucet_config_file, 'fconfig')
        switches_config = {str(dp): dp for dp in dps_config}

        self._acl_collector = AclStateCollector()
        self._acl_collector.update_switch_configs(switches_config)

    def tearDown(self):
        """Cleanup after each test method finishes"""
        shutil.rmtree(self._temp_dir)
        self._acl_collector = None


class SimpleAclStateCollectorTestCase(AclStateCollectorTestBase):
    """Basic AclStateCollector tests"""

    FAUCET_CONFIG = """
    dps:
      sec:
        dp_id: 10
        interfaces:
          1:
            acl_in: port_1_acl
            native_vlan: 1000
    acls:
      port_1_acl:
      - rule:
        description: allow all
        cookie: 5
        actions:
          allow: True
    """

    ACL_SAMPLES = [
        MockSample({'dp_name': 'sec', 'in_port': '1', 'cookie': 5}, 20)
    ]

    def test_get_port_acl_count(self):
        """Test getting the port ACL count"""
        acl_count = self._acl_collector.get_port_acl_count('sec', 1, self.ACL_SAMPLES)
        expected_acl_count = {
            'rules': {
                'allow all': {
                    'packet_count': 20
                }
            }
        }
        self.assertEqual(acl_count, expected_acl_count)


if __name__ == '__main__':
    unittest.main()
