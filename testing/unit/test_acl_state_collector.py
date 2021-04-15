"""Unit tests for AclStateCollector"""

from __future__ import absolute_import

import shutil
import tempfile
import unittest

from acl_state_collector import AclStateCollector
from utils import dict_proto

from proto.acl_counting_pb2 import RuleCounts

from faucet import config_parser


class MockSample:
    """Mocking the metric samples"""
    def __init__(self, labels, value):
        self.labels = labels
        self.value = value


class AclStateCollectorTestBase(unittest.TestCase):
    """Base setup for AclStateCollector tests"""

    FAUCET_CONFIG = ''
    RULE_SAMPLES = []

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

    def _verify_rule_counts(self, rule_counts, expected_rule_counts):
        self.assertEqual(rule_counts, dict_proto(expected_rule_counts, RuleCounts))


class SimpleAclStateCollectorTestCase(AclStateCollectorTestBase):
    """Basic AclStateCollector tests"""

    FAUCET_CONFIG = """
    dps:
      sec:
        dp_id: 10
        interfaces:
          1:
            acl_in: port_1_acl
            native_vlan: 1001
          2:
            acl_in: port_2_acl
            native_vlan: 1002
    acls:
      port_1_acl:
      - rule:
        description: allow dns
        cookie: 4
        actions:
          allow: True
      - rule:
        description: allow all
        cookie: 5
        actions:
          allow: True
      port_2_acl:
      - rule:
        description: allow icmp
        cookie: 6
        actions:
          allow: True
      - rule:
        description: allow ntp
        cookie: 7
        actions:
          allow: True
      - rule:
        description: allow all
        actions:
          allow: True
    """

    RULE_SAMPLES = [
        MockSample({'dp_name': 'sec', 'in_port': '1', 'cookie': 4}, 24),
        MockSample({'dp_name': 'sec', 'in_port': '1', 'cookie': 5}, 25),
        MockSample({'dp_name': 'sec', 'in_port': '2', 'cookie': 6}, 26)
    ]

    def test_get_port_rule_counts(self):
        """Test getting the port ACL rule count"""
        rule_counts = self._acl_collector.get_port_rule_counts('sec', 1, self.RULE_SAMPLES)
        expected_rule_counts = {
            'rules': {
                'allow dns': {'packet_count': 24},
                'allow all': {'packet_count': 25}
            }
        }
        self._verify_rule_counts(rule_counts, expected_rule_counts)

    def test_rule_errors(self):
        """Test getting the rule_counts that contains rule errors"""
        rule_counts = self._acl_collector.get_port_rule_counts('sec', 2, self.RULE_SAMPLES)
        expected_rule_counts = {
            'rules': {
                'allow icmp': {'packet_count': 26}
            },
            'errors': [
                'No ACL metric sample available for switch, port, ACL, rule: sec, 2, port_2_acl, '
                'allow ntp (cookie=7)'
            ]
        }
        self._verify_rule_counts(rule_counts, expected_rule_counts)

    def test_nonexistent_port_config(self):
        """Testing getting rule counts for a nonexistent port"""
        rule_counts = self._acl_collector.get_port_rule_counts('sec', 3, self.RULE_SAMPLES)
        expected_rule_counts = {
            'errors': ['Port not defined in Faucet dps config: sec, 3']
        }
        self._verify_rule_counts(rule_counts, expected_rule_counts)


if __name__ == '__main__':
    unittest.main()
