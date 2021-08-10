"""Unit tests for session server"""

from __future__ import absolute_import
import copy
import unittest
from unittest.mock import create_autospec

from udmi_manager import UdmiManager
from runner import Device

from udmi.agent.mqtt_manager import MqttManager

from proto.report_pb2 import DeviceReport

class UdmiDiscoverBase(unittest.TestCase):
    """Base tests for UDMI discovery"""

    UDMI_CONFIG = {
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
        self._udmi = UdmiManager(self.UDMI_CONFIG, mqtt_factory=self._mock_mqtt_manager)


class UdmiDiscoveryTest(UdmiDiscoverBase):
    """Basic discovery tests"""

    def test_discovery_send(self):
        """Test that sending works when there's something to send"""
        device = Device()
        self._udmi.discovery(device)
        self._mqtt.publish.assert_not_called()
        device.mac = '123435'
        self._udmi.discovery(device)
        self._mqtt.publish.assert_called_once()


class UdmiEmptyConfigTest(UdmiDiscoverBase):
    """Base test for empty configiration"""

    # Create a copy config that doesn't have project_id defined.
    UDMI_CONFIG = copy.deepcopy(UdmiDiscoverBase.UDMI_CONFIG)
    del UDMI_CONFIG['cloud_config']['project_id']

    def test_no_manager(self):
        """Test the case when there is an empty configuraiton"""
        self.assertIsNone(self._mqtt)

        # These calls should simply not throw an exception in this case.
        device = Device()
        device.mac = '123435'
        self._udmi.discovery(device)

        report = DeviceReport()
        self._udmi.report(report)
