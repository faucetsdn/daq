"""Unit tests for device testing client"""

import time
import unittest

from forch.device_testing_server import DeviceTestingServer

from device_testing_client import DeviceTestingClient
from utils import proto_dict


class DeviceTestingClientTestBase(unittest.TestCase):
    """Base class for device testing client unit test"""
    _SERVER_ADDRESS = '0.0.0.0'
    _SERVER_PORT = 50051

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server = None
        self._client = None

    def _process_device_testing_state(self, device_testing_state):
        pass

    def setUp(self):
        """Setup fixture for each test method"""
        self._client = DeviceTestingClient()

        self._server = DeviceTestingServer(
            self._process_device_testing_state, self._SERVER_ADDRESS, self._SERVER_PORT)
        self._server.start()

    def tearDown(self):
        """Cleanup after each test method finishes"""
        self._server.stop()


class DeviceTestingClientBasicTestCase(DeviceTestingClientTestBase):
    """Basic test case for device testing client"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._received_states = []

    def _process_device_testing_state(self, device_testing_state):
        self._received_states.append(
            proto_dict(device_testing_state, including_default_value_fields=True))

    def test_sending_device_testing_states(self):
        """Test behavior of the client and server when client sends device testing states"""
        expected_testing_states = [
            {'mac': '00:0X:00:00:00:01', 'port_behavior': 'unknown'},
            {'mac': '00:0Y:00:00:00:02', 'port_behavior': 'passed'},
            {'mac': '00:0Z:00:00:00:03', 'port_behavior': 'cleared'},
            {'mac': '00:0A:00:00:00:04', 'port_behavior': 'passed'},
            {'mac': '00:0B:00:00:00:05', 'port_behavior': 'unknown'}
        ]

        for testing_state in expected_testing_states:
            print(f'Sending device testing state:\n{testing_state}')
            mac = testing_state['mac']
            testing_result = testing_state['port_behavior']
            server_result = self._client.send_testing_result(mac, testing_result)
            print(f'Received {server_result} from server')

        time.sleep(2)
        self.assertEqual(self._received_states, expected_testing_states)
