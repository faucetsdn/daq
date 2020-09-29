"""Unit tests for configurator"""

import logging
import unittest
import sys
import os
import time
from unittest.mock import MagicMock, mock_open, patch
from daq.runner import DAQRunner, configurator, PortInfo
from daq.host import ConnectedHost
import network

import grpc

from forch.device_testing_server import DeviceTestingServer
from forch.proto.shared_constants_pb2 import PortBehavior

from device_testing_client import DeviceTestingClient

logger = logging.getLogger()
logger.level = logging.INFO
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


class TestRunnerBase(unittest.TestCase):
    """Test class for Configurator"""

    config = {
        'monitor_scan_sec' : '30',
        'default_timeout_sec' : '350',
        'base_conf' : 'resources/setups/baseline/module_config.json',
        'site_path' : 'local/site/',
        'initial_dhcp_lease_time' : '120s',
        'dhcp_lease_time' : '500s',
        'long_dhcp_response_sec' : '105'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runner = None

    def setUp(self):
        os.environ = {
            **os.environ,
            "DAQ_VERSION": "",
            "DAQ_LSB_RELEASE": "",
            "DAQ_SYS_UNAME": ""
        }
        configurator.Configurator.load_and_merge = MagicMock(return_value={})
        network.TestNetwork.__init__ = MagicMock(return_value=None)
        DAQRunner._get_test_metadata = MagicMock(return_value={})
        with patch("builtins.open", mock_open(read_data="data")):
            self.runner = DAQRunner(self.config)


class TestRunnerReapStatePorts(TestRunnerBase):
    """Test class for Configurator"""

    def test_reap_stale_ports(self):
        """Test port flap timeout config override"""
        self.runner.target_set_error = MagicMock()
        device = self.runner._devices.new_device("0000000000", None)
        self.runner._reap_stale_ports()
        self.runner.target_set_error.assert_not_called()
        ConnectedHost.__init__ = MagicMock(return_value=None)
        host = ConnectedHost()
        host.test_name = "test_test"
        device.port.flapping_start = time.time() - 1
        device.host = host

        host.get_port_flap_timeout = MagicMock(return_value=10000)
        self.runner._reap_stale_ports()
        self.runner.target_set_error.assert_not_called()

        host.get_port_flap_timeout = MagicMock(return_value=None)
        self.runner._reap_stale_ports()
        host.get_port_flap_timeout.assert_called_with(host.test_name)
        self.runner.target_set_error.assert_called()


class TestRunnerSendingTestingResult(TestRunnerBase):
    """Test case to test the runner sending device testing result to the device testing server"""

    _SERVER_ADDRESS = '0.0.0.0'
    _SERVER_PORT = 50051

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config['device_testing_server_port'] = 50051

        channel = grpc.insecure_channel(f'{self._SERVER_ADDRESS}:{self._SERVER_PORT}')
        self._client = DeviceTestingClient(channel)

        self._server = DeviceTestingServer(
            self._process_device_testing_state, self._SERVER_ADDRESS, self._SERVER_PORT)
        self._server.start()

        self._received_results = []

    def tearDown(self):
        """Cleanup after each test method finishes"""
        self._server.stop()

    def _process_device_testing_state(self, device_testing_state):
        self._received_results.append(
            (device_testing_state.mac, device_testing_state.port_behavior))

    def test_target_device_complete(self):
        """Test behavior of the runner and testing client when a device testing finishes"""
        device = self.runner._devices.new_device("0000000000", None)
        self.runner._target_set_finalize(device, {}, "Target device termination")

        time.sleep(2)
        expected_testing_results = [("00:00:00:00:00:00", PortBehavior.passed)]
        self.assertEqual(self._received_results, expected_testing_results)


if __name__ == '__main__':
    unittest.main()
