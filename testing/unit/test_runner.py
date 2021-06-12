"""Unit tests for configurator"""

import logging
import os
import sys
import time
import unittest
from unittest.mock import MagicMock, mock_open, patch

import network

from forch.proto.shared_constants_pb2 import PortBehavior
from forch.proto.devices_state_pb2 import DevicePortEvent

from daq.host import ConnectedHost
from daq.runner import DAQRunner, configurator

LOGGER = logging.getLogger()
LOGGER.level = logging.INFO
STREAM_HANDLER = logging.StreamHandler(sys.stdout)
LOGGER.addHandler(STREAM_HANDLER)


# pylint: disable=protected-access
class TestRunner(unittest.TestCase):
    """Test class for Configurator"""

    config = {
        'monitor_scan_sec' : '30',
        'default_timeout_sec' : '350',
        'base_conf' : 'resources/setups/baseline/base_config.json',
        'site_path' : 'local/site/',
        'initial_dhcp_lease_time' : '120s',
        'dhcp_lease_time' : '500s',
        'long_dhcp_response_sec' : '105',
        'run_trigger': {
            'max_hosts': 2
        }
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
        with patch("builtins.open", mock_open(read_data="a: b")):
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
        mock_port_event = DevicePortEvent(state=PortBehavior.PortState.down)
        self.runner._handle_remote_port_state(device, mock_port_event)
        self.runner._reap_stale_ports()
        self.runner.target_set_error.assert_not_called()

        ConnectedHost.__init__ = MagicMock(return_value=None)
        host = ConnectedHost()
        host.test_name = "test_test"
        device.host = host
        host.get_port_flap_timeout = MagicMock(return_value=10000)
        port_up_event = DevicePortEvent(state=PortBehavior.PortState.up,
                                        device_vlan=1, assigned_vlan=2)
        port_down_event = DevicePortEvent(state=PortBehavior.PortState.down)

        self.runner._handle_remote_port_state(device, port_up_event)

        self.runner._reap_stale_ports()
        self.runner.target_set_error.assert_not_called()

        host.get_port_flap_timeout = MagicMock(return_value=None)
        self.runner._handle_remote_port_state(device, port_down_event)

        self.runner._handle_remote_port_state(device, port_up_event)

        self.runner._reap_stale_ports()
        self.runner.target_set_error.assert_not_called()

        self.runner._handle_remote_port_state(device, port_down_event)

        self.runner._reap_stale_ports()
        host.get_port_flap_timeout.assert_called_with(host.test_name)
        self.runner.target_set_error.assert_called()

    def test_target_set_queue_capacity(self):
        """Test the target set running queue"""
        self.runner._system_active = True

        device1 = self.runner._devices.new_device("0000000001", None)
        device2 = self.runner._devices.new_device("0000000002", None)
        device3 = self.runner._devices.new_device("0000000003", None)
        device4 = self.runner._devices.new_device("0000000004", None)
        device5 = self.runner._devices.new_device("0000000005", None)

        def activate_device(device):
            device.host = True

        self.runner._target_set_activate = MagicMock(side_effect=activate_device)

        self.runner._target_set_trigger(device1)
        self.runner._target_set_trigger(device2)
        self.runner._target_set_trigger(device3)
        self.runner._target_set_trigger(device4)
        self.assertEqual(self.runner._target_set_activate.call_count, 2)
        self.assertTrue(device1.host)
        self.assertTrue(device2.host)
        self.assertFalse(device3.host)

        self.assertEqual(len(self.runner._target_set_queue), 2)

        device2.host = False
        self.runner._target_set_consider()
        self.assertEqual(self.runner._target_set_activate.call_count, 3)
        self.assertTrue(device3.host)

        self.runner._target_set_trigger(device4)
        self.runner._target_set_trigger(device5)
        self.runner._target_set_consider()
        self.assertEqual(self.runner._target_set_activate.call_count, 3)
        self.assertEqual(len(self.runner._target_set_queue), 2)

        self.runner._target_set_cancel(device4)
        device1.host = False
        self.runner._target_set_consider()
        self.assertEqual(self.runner._target_set_activate.call_count, 4)
        self.assertEqual(len(self.runner._target_set_queue), 0)
        self.assertFalse(device4.host)
        self.assertTrue(device5.host)

if __name__ == '__main__':
    unittest.main()
