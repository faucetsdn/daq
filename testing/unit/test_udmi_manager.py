"""Unit tests for session server"""

from __future__ import absolute_import
import copy
import unittest
from unittest.mock import create_autospec

from udmi_manager import UdmiManager
from runner import Device

from udmi.agent.mqtt_manager import MqttManager

class UdmiDiscoverBase(unittest.TestCase):
    """Base tests for UDMI discovery"""

    BASE_CONFIG = {
        'cloud_config': {
            'cloudRegion': 'us_west1',
            'project_id': 'hello'
        }
    }

    def _mock_mqtt_manager(self, config, on_message=None):
        self._mqtt = create_autospec(MqttManager)
        return self._mqtt

    def setUp(self):
        self._mqtt = None
        print('Config is %s', self.BASE_CONFIG)
        self._udmi = UdmiManager(self.BASE_CONFIG, mqtt_factory=self._mock_mqtt_manager)


class UdmiDiscoverTest(UdmiDiscoverBase):
    """Basic discovery tests"""

    def test_basic_send(self):
        """Test that sending works when there's something to send"""
        device = Device()
        self._udmi.discovery(device)
        self._mqtt.publish.assert_not_called()
        device.mac = '123435'
        self._udmi.discovery(device)
        self._mqtt.publish.assert_called_once()


class UdmiEmptyConfigTest(UdmiDiscoverBase):
    """Base test for empty configiration"""

    BASE_CONFIG = copy.deepcopy(UdmiDiscoverBase.BASE_CONFIG)
    del BASE_CONFIG['cloud_config']['project_id']

    def test_no_manager(self):
        """Test the case when there is an empty configuraiton"""
        self.assertIsNone(self._mqtt)
