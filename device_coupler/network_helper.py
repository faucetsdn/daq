"""Module to create n/w setup for device coupler"""

from __future__ import absolute_import
from device_coupler.ovs_helper import OvsHelper
from device_coupler.utils import get_logger

import argparse


class NetworkHelper():
    """Network setup helper for device coupler"""

    def __init__(self, trunk_iface, bridge, test_vlans):
        self._ovs_helper = OvsHelper()
        self._logger = get_logger('networkhelper')
        self._trunk_iface = trunk_iface
        self._bridge = bridge
        self._test_vlans = test_vlans

    def setup(self):
        """Setup n/w"""
        self._logger.info('Setting up device coupler network.')
        self._setup_ovs_bridge()

    def cleanup(self):
        """Clean up n/w"""
        self._delete_ovs_bridge()
        self._logger.info('Cleaned up device coupler network.')

    def _setup_ovs_bridge(self):
        self._ovs_helper.create_ovs_bridge(self._bridge)
        self._ovs_helper.add_iface_to_bridge(self._bridge, self._trunk_iface)
        self._ovs_helper.set_trunk_vlan(self._trunk_iface, self._test_vlans)

    def _delete_ovs_bridge(self):
        self._ovs_helper.delete_ovs_bridge(self._bridge)

    def get_ovs_bridge(self):
        return self._bridge


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bridge', help="Name of OVS bridge", type=str)
    parser.add_argument('--trunk-iface', help="Name of trunk interface", type=str)

    args = parser.parse_args()
    trunk_iface = args.trunk_iface
    bridge = args.bridge
    nw_helper = NetworkHelper(trunk_iface, bridge)
    nw_helper.setup()
    pass


if __name__ == "__main__":
    main()
