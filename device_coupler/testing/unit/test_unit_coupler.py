from __future__ import absolute_import

import unittest

from device_coupler.ovs_helper import OvsHelper


class TestOvsHelper(unittest.TestCase):

    def _create_netns_with_veth_pair(self, index):
        ovs = OvsHelper()
        iface1 = 'dev%s' % index
        iface2 = 'netns0'
        vnet = 'vnet%s' % index
        ovs.create_veth_pair(iface1, iface2)
        ovs._run_shell('sudo ip netns add %s' % vnet)
        ovs._run_shell('sudo ip link set %s netns %s' % (iface2, vnet))
        ovs._run_shell('sudo ip -n %s addr add 10.1.1.%s/24 dev %s' % (vnet, index, iface2))
        ovs._run_shell('sudo ip -n %s link set %s up' % (vnet, iface2))

    def _delete_netns(self, vnet):
        ovs = OvsHelper()
        ovs._run_shell('sudo ip netns del %s' % vnet)

    def test_ovs_bridge_vlan(self):
        ovs = OvsHelper()
        bridge = 'test_br'
        ovs.create_ovs_bridge(bridge)
        for index in range(1,5):
            self._create_netns_with_veth_pair(index)
            iface = 'dev%s' % index
            tag = 200 + index % 2
            ovs.add_iface_to_bridge(bridge, iface)
            ovs.set_native_vlan(iface, tag)
        retcode, _, _ = ovs._run_shell_no_raise('sudo ip netns exec vnet1 ping -c 3 10.1.1.3')
        self.assertEqual(retcode, 0)
        retcode, _, _ = ovs._run_shell_no_raise('sudo ip netns exec vnet1 ping -c 3 10.1.1.4')
        self.assertEqual(retcode, 1)
        for index in range(1,5):
            vnet = 'vnet%s' % index
            self._delete_netns(vnet)
        ovs.delete_ovs_bridge(bridge)
