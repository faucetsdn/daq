"""Script that creates an OVS access switch with devices."""

from __future__ import absolute_import
from ovs_helper import OvsHelper


ovs_helper = OvsHelper()


def add_devices_to_br(bridge, device_range):
    """Assumes faux indexes are in namespace"""
    for index in device_range:
        #ovs_helper.create_faux_device(index)
        iface = "faux-%s" % index
        ovs_helper.add_iface_to_bridge(bridge, iface)
        ovs_helper.set_native_vlan(iface, 200 + (index % 3) * 10)


def main():
    bridge = 'br0'
    num_devices = 3
    ovs_helper.create_ovs_bridge(bridge)
    add_devices_to_br(bridge, range(1,num_devices+1))
    ovs_helper.create_veth_pair('trunk0', 'trunk1')
    ovs_helper.add_iface_to_bridge(bridge, 'trunk0')


if __name__ == "__main__":
    main()
