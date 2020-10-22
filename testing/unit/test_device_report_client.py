"""Unit tests for device report client"""

import time
import unittest

from forch.device_report_server import DeviceReportServer

from device_report_client import DeviceReportClient
from utils import proto_dict


class DeviceReportClientTestBase(unittest.TestCase):
    """Base class for device report client unit test"""
    _SERVER_ADDRESS = '0.0.0.0'
    _SERVER_PORT = 50071

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server = None
        self._client = None

    def _process_result(self, result):
        pass

    def setUp(self):
        """Setup fixture for each test method"""
        self._client = DeviceReportClient(server_port=self._SERVER_PORT)

        self._server = DeviceReportServer(
            self._process_result, self._SERVER_ADDRESS, self._SERVER_PORT)
        self._server.start()

    def tearDown(self):
        """Cleanup after each test method finishes"""
        self._server.stop()


class DeviceDeviceReportServerlientBasicTestCase(DeviceReportClientTestBase):
    """Basic test case for device report client"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._received_results = []

    def _process_result(self, result):
        devices_state_map = proto_dict(result, including_default_value_fields=True)
        mac, device_behavior = devices_state_map['device_mac_behaviors'].popitem()
        received_result = {'mac': mac, 'port_behavior': device_behavior['port_behavior']}
        self._received_results.append(received_result)

    def test_sending_device_result(self):
        """Test behavior of the client and server when client sends devices states"""
        expected_results = [
            {'mac': '00:0X:00:00:00:01', 'port_behavior': 'unknown'},
            {'mac': '00:0Y:00:00:00:02', 'port_behavior': 'passed'},
            {'mac': '00:0Z:00:00:00:03', 'port_behavior': 'cleared'},
            {'mac': '00:0A:00:00:00:04', 'port_behavior': 'passed'},
            {'mac': '00:0B:00:00:00:05', 'port_behavior': 'unknown'}
        ]

        for result in expected_results:
            print(f'Sending result:\n{result}')
            self._client.send_device_result(result['mac'], result['port_behavior'])

        time.sleep(2)
        self.assertEqual(self._received_results, expected_results)
