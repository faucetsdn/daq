"""Unit tests for network"""

import os
import logging
import sys
import time
import unittest
from unittest.mock import MagicMock, mock_open, patch
from forch import faucetizer

from runner import Devices
import network
import topology
from daq.proto.session_server_pb2 import TunnelEndpoint

LOGGER = logging.getLogger()
LOGGER.level = logging.INFO
STREAM_HANDLER = logging.StreamHandler(sys.stdout)
LOGGER.addHandler(STREAM_HANDLER)

class FakeSwitch:
    name = "Fake switch"
    cmd = lambda *args: None
    vsctl = lambda *args: None

# pylint: disable=protected-access
class TestNetwork(unittest.TestCase):
    """Test class for Configurator"""

    config = {
        'device_reporting': {
            'server_port': 8080
        },
        'switch_setup': {
            'uplink_port': 1
        }
    }

    def setUp(self):
        os.environ = {
            **os.environ,
            'DAQ_LIB': '',
            'DAQ_CONF': '',
            'DAQ_RUN': ''
        }
        faucetizer.Faucetizer.__init__ = MagicMock(return_value=None)
        topology.FaucetTopology._run_faucet = MagicMock(return_value=None)

    def test_configure_remote_tap_with_no_device_session(self):
        """Test port flap timeout config override"""
        net = network.TestNetwork(self.config)
        net.sec = FakeSwitch()
        net.sec.cmd = MagicMock(return_value=None)
        device = Devices().new_device("mac")
        net._configure_remote_tap(device)
        self.assertFalse(net._vxlan_port_sets)
        net.sec.cmd.assert_not_called()

    def test_cleanup_remote_tap_with_no_device_session(self):
        """Test port flap timeout config override"""
        net = network.TestNetwork(self.config)
        net.sec = FakeSwitch()
        net.sec.cmd = MagicMock(return_value=None)
        device = Devices().new_device("mac")
        net._cleanup_remote_tap(device)
        self.assertFalse(net._vxlan_port_sets)
        net.sec.cmd.assert_not_called()

    def test_configure_remote_tap_simple(self):
        """Test port flap timeout config override"""
        net = network.TestNetwork(self.config)
        net.sec = FakeSwitch()
        net.sec.cmd = MagicMock(return_value=None)
        device = Devices().new_device("mac")
        device.session_endpoint = TunnelEndpoint()
        net._configure_remote_tap(device)
        self.assertEqual(net._vxlan_port_sets, set([2]))
        net.sec.cmd.assert_any_call('ip link set vxlan2 up')
        self.assertEqual(device.port.vxlan, 2)

        net._cleanup_remote_tap(device)
        self.assertFalse(net._vxlan_port_sets)
        net.sec.cmd.assert_any_call('ip link set vxlan2 down')
        net.sec.cmd.assert_any_call('ip link del vxlan2')

    def test_configure_remote_tap(self):
        """Test port flap timeout config override"""
        net = network.TestNetwork(self.config)
        net.sec = FakeSwitch()
        net.sec.cmd = MagicMock(return_value=None)
        device1 = Devices().new_device("mac")
        device1.session_endpoint = TunnelEndpoint()
        net._configure_remote_tap(device1)

        device2 = Devices().new_device("mac")
        device2.session_endpoint = TunnelEndpoint()
        net._configure_remote_tap(device2)

        self.assertEqual(net._vxlan_port_sets, set([2, 3]))
        net._cleanup_remote_tap(device1)
        self.assertEqual(net._vxlan_port_sets, set([3]))

        device3 = Devices().new_device("mac")
        device3.session_endpoint = TunnelEndpoint()
        net._configure_remote_tap(device3)
        self.assertEqual(net._vxlan_port_sets, set([2, 3]))
        net._configure_remote_tap(device1)
        self.assertEqual(net._vxlan_port_sets, set([2, 3, 4]))

if __name__ == '__main__':
    unittest.main()
