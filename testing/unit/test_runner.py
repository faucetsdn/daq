"""Unit tests for configurator"""

import unittest
import sys
import os
import time
from unittest.mock import MagicMock, mock_open, patch

from forch.proto.shared_constants_pb2 import PortBehavior
from forch.proto.devices_state_pb2 import DevicePortEvent

from daq.runner import DAQRunner, configurator, PortInfo
from daq.host import ConnectedHost
import network

import logging
logger = logging.getLogger()
logger.level = logging.INFO
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

class TestRunner(unittest.TestCase):
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

    def test_reap_stale_ports_with_remote_ports(self):
        """Test device learn on vlan trigger"""
        self.runner.target_set_error = MagicMock()
        device = self.runner._devices.new_device("0000000000", None)
        mock_port_event = DevicePortEvent(timestamp="1", event=PortBehavior.PortEvent.down)
        self.runner._handle_remote_port_state(device, mock_port_event)
        self.runner._reap_stale_ports()
        self.runner.target_set_error.assert_not_called()

        ConnectedHost.__init__ = MagicMock(return_value=None)
        host = ConnectedHost()
        host.test_name = "test_test"
        device.host = host
        host.get_port_flap_timeout = MagicMock(return_value=10000)
        mock_port_event = DevicePortEvent(timestamp="1", event=PortBehavior.PortEvent.up)
        self.runner._handle_remote_port_state(device, mock_port_event)

        self.runner._reap_stale_ports()
        self.runner.target_set_error.assert_not_called()

        host.get_port_flap_timeout = MagicMock(return_value=None)
        mock_port_event = DevicePortEvent(timestamp="1", event=PortBehavior.PortEvent.down)
        self.runner._handle_remote_port_state(device, mock_port_event)

        mock_port_event = DevicePortEvent(timestamp="1", event=PortBehavior.PortEvent.up)
        self.runner._handle_remote_port_state(device, mock_port_event)

        self.runner._reap_stale_ports()
        self.runner.target_set_error.assert_not_called()

        mock_port_event = DevicePortEvent(timestamp="1", event=PortBehavior.PortEvent.down)
        self.runner._handle_remote_port_state(device, mock_port_event)

        self.runner._reap_stale_ports()
        host.get_port_flap_timeout.assert_called_with(host.test_name)
        self.runner.target_set_error.assert_called()

if __name__ == '__main__':
    unittest.main()
