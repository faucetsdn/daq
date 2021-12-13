"""Module to create n/w setup for device coupler"""

from __future__ import absolute_import
from ovs_helper import OvsHelper
from device_coupler.utils import get_logger


class NetworkHelper():
    """Network setup helper for device coupler"""

    def __init__(self, trunk_iface, bridge):
        self._ovs_helper = OvsHelper()
        self._logger = get_logger('networkhelper')
        self._trunk_iface = trunk_iface
        self._bridge = bridge

    def setup(self):
        """Setup n/w"""
        self._setup_ovs_bridge()

    def cleanup(self):
        """Clean up n/w"""
        self._delete_ovs_bridge()

    def _setup_ovs_bridge(self):
        self._ovs_helper.create_ovs_bridge(self._bridge)
        self._ovs_helper.add_iface_to_bridge(self._bridge, self._trunk_iface)

    def _delete_ovs_bridge(self):
        self._ovs_helper.delete_ovs_bridge(self._bridge)

    def get_ovs_bridge(self):
        return self._bridge


def main():
    trunk_iface = 'trunk1'
    bridge = 'dev_br0'
    nw_helper = NetworkHelper(trunk_iface, bridge)
    nw_helper.setup()
    pass


if __name__ == "__main__":
    main()
