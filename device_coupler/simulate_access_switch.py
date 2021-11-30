"""Script that creates an OVS access switch with devices."""

from __future__ import absolute_import
from ovs_helper import OvsHelper


ovs_helper = OvsHelper()


def add_devices_to_br(bridge, num_devices):
    for index in range(1, num_devices + 1):
        ovs_helper.create_faux_device(index)
        iface = "faux-%s" % index
        ovs_helper.add_iface_to_bridge(bridge, iface)
        ovs_helper.set_native_vlan(iface, 200 + index * 10)


def main():
    bridge = 'br0'
    num_devices = 3
    ovs_helper.create_ovs_bridge(bridge)
    add_devices_to_br(bridge, num_devices)


if __name__ == "__main__":
    main()
