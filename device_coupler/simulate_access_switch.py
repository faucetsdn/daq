"""Script that creates an OVS access switch with devices."""

from __future__ import absolute_import
from ovs_helper import OvsHelper

import argparse


ovs_helper = OvsHelper()


def add_devices_to_br(bridge, device_range):
    """Assumes faux indexes are in namespace"""
    for index in device_range:
        iface = "faux-%s" % index
        ovs_helper.add_iface_to_bridge(bridge, iface)
        ovs_helper.set_native_vlan(iface, 200 + (index) * 10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bridge', help="Name of OVS bridge", type=str)
    parser.add_argument('--devices', help="Number of faux devices", type=int)
    parser.add_argument('--trunk-iface', help="Name of trunk interface", type=str)

    args = parser.parse_args()

    bridge = args.bridge
    num_devices = args.devices
    trunk_iface = args.trunk_iface
    ovs_helper.create_ovs_bridge(bridge)
    add_devices_to_br(bridge, list(range(1, num_devices + 1)))
    local_trunk_iface = 'trunk0' if trunk_iface == 'trunk1' else 'trunk1'
    ovs_helper.create_veth_pair(local_trunk_iface, trunk_iface)
    ovs_helper.add_iface_to_bridge(bridge, local_trunk_iface)


if __name__ == "__main__":
    main()
