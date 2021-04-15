"""Unit tests for device report client"""

import os
import time
import unittest
from unittest.mock import patch

from forch.device_report_server import DeviceReportServer, DeviceReportServicer
from forch.proto.shared_constants_pb2 import PortBehavior
from forch.proto.devices_state_pb2 import DevicePortEvent

from device_report_client import DeviceReportClient
from utils import proto_dict


class DeviceReportClientTestBase(unittest.TestCase):
    """Base class for device report client unit test"""
    _SERVER_ADDRESS = '0.0.0.0'
    _SERVER_PORT = 50071

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.environ['FORCH_LOG'] = '/tmp/forch.log'
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


class DeviceDeviceReportServerlientPortEventsTestCase(DeviceReportClientTestBase):
    """Port events for device report client"""
    _SERVER_PORT2 = 50072

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._received_port_events = []
        self._mock_port_events = [
            DevicePortEvent(state=PortBehavior.PortState.down),
            DevicePortEvent(state=PortBehavior.PortState.down),
            DevicePortEvent(state=PortBehavior.PortState.up),
            DevicePortEvent(state=PortBehavior.PortState.down)
        ]

    def setUp(self):
        """Setup fixture for each test method"""
        self._client = DeviceReportClient(server_port=self._SERVER_PORT2)

        def mock_function(_, __, ___):
            for event in self._mock_port_events:
                yield event
        with patch.object(DeviceReportServicer, 'GetPortState', side_effect=mock_function,
                          autospec=True):
            self._server = DeviceReportServer(
                self._process_result, self._SERVER_ADDRESS, self._SERVER_PORT2)
            self._server.start()

    def _on_port_event(self, event):
        self._received_port_events.append(event)

    def test_getting_port_events(self):
        """Test the ability to get port events"""
        self._client.connect("mac", self._on_port_event)
        time.sleep(1)
        self.assertEqual(self._received_port_events, self._mock_port_events)


class DeviceDeviceReportPortEventsWithTestResultsTestCase(DeviceReportClientTestBase):
    """Port events for device report client"""
    _SERVER_PORT = 50073

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._received_port_events = []

    def _on_port_event(self, event):
        self._received_port_events.append(event)

    def test_sending_test_results_terminate_port_events(self):
        """Test the ability to get port events"""
        self._server.process_port_learn("name", "port", "mac", 1)
        self._client.connect("mac", self._on_port_event)
        time.sleep(1)  # Takes time to start grpc stream in a thread
        self._server.process_port_state("name", "port", False)
        self._server.process_port_state("name", "port", True)
        self._client.send_device_result("mac", "passed")
        self.assertEqual(len(self._received_port_events), 3)


class DeviceDeviceReportPortEventsStreamCleanup(DeviceReportClientTestBase):
    """Port events for device report client"""
    _SERVER_PORT = 50074

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._received_port_events = []

    def _on_port_event(self, event):
        self._received_port_events.append(event)

    def test_client_terminating_port_events(self):
        """Test the ability to get port events"""
        self._server.process_port_learn("name", "port", "mac", 1)
        self._client.connect("mac", self._on_port_event)
        time.sleep(1)
        self._server.process_port_state("name", "port", False)
        time.sleep(1)
        self._client.terminate()
        time.sleep(1)
        self._server.process_port_state("name", "port", False)
        self.assertEqual(len(self._received_port_events), 2)


class DeviceDeviceReportPortEventsMultipleStreams(DeviceReportClientTestBase):
    """Port events for device report client"""
    _SERVER_PORT = 50075

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._received_port_events = []
        self._received_port_events2 = []

    def _on_port_event(self, event):
        self._received_port_events.append(event)

    def _on_port_event2(self, event):
        self._received_port_events2.append(event)

    def test_sending_test_results_terminate_multiple_port_events(self):
        """Test the ability to get port events"""
        self._server.process_port_learn("name", "port", "mac", 1)
        self._client.connect("mac", self._on_port_event)
        self._client.connect("mac", self._on_port_event2)
        time.sleep(1)
        self._server.process_port_state("name", "port", False)
        self._server.process_port_state("name", "port", True)
        self._client.send_device_result("mac", "passed")
        time.sleep(1)
        self.assertEqual(len(self._received_port_events), 3)
        self.assertEqual(len(self._received_port_events2), 3)
