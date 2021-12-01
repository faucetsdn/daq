"""Module to help setup OVS bridges, VxLANs and other virt network components"""

from __future__ import absolute_import, division

from functools import partial
from python_lib.shell_command_helper import ShellCommandHelper
from utils import get_logger


class OvsHelper:
    """Class to build OVS bridges, VxLANs and other network components"""
    DEFAULT_VXLAN_PORT = 4789
    VXLAN_CMD_FMT = 'ip link add %s type vxlan id %s remote %s dstport %s srcport %s %s nolearning'

    def __init__(self):
        self._logger = get_logger('OvsHelper')
        self._run_shell = partial(ShellCommandHelper().run_cmd, capture=True)
        self._run_shell_no_raise = partial(ShellCommandHelper().run_cmd, capture=True, strict=False)

    def create_vxlan_endpoint(self, interface, remote_ip, vni, local_vtep_ip=None):
        """Creates a VxLAN endpoint"""
        interface = "vxlan%s" % port
        self.remove_vxlan_endpoint(interface)
        self._logger.info("Creating VxLAN endpoint %s", interface)
        vxlan_cmd = 'sudo ' + self.VXLAN_CMD_FMT % (
            interface, vni, remote_ip, self.DEFAULT_VXLAN_PORT,
            self.DEFAULT_VXLAN_PORT, self.DEFAULT_VXLAN_PORT)
        self._run_shell(vxlan_cmd)
        self._run_shell('sudo ip link set %s up' % interface)
        if local_vtep_ip:
            self._run_shell('sudo ip addr add %s dev %s' % (local_vtep_ip, interface))
        return interface

    def remove_vxlan_endpoint(self, interface, bridge):
        """Clears VxLAN endpoint"""
        self._logger.info('Removing vxlan interface %s', interface)
        self._run_shell_no_raise('sudo ip link set %s down' % interface)
        self._run_shell_no_raise('sudo ip link del %s' % interface)
        self._run_shell_no_raise('sudo ovs-vsctl del-port %s %s' % (bridge, interface))

    def create_ovs_bridge(self, name):
        """Creates OVS bridge"""
        self._logger.info('Creating OVS bridge %s', name)
        self._run_shell('sudo ovs-vsctl add-br %s' % name)

    def delete_ovs_bridge(self, name):
        """Delete ovs bridge"""
        self._logger.info('Deleting OVS bridge %s', name)
        self._run_shell_no_raise('sudo ovs-vsctl del-br %s' % name)

    def add_iface_to_bridge(self, bridge, iface):
        """Add interface to OVS bridge"""
        self._logger.info('Adding interface %s to bridge %s', iface, bridge)
        self._run_shell('sudo ovs-vsctl add-port %s %s' % (bridge, iface))

    def set_native_vlan(self, interface, vlan):
        """Set native VLAN to port on OVS bridge"""
        self._logger.info('Enabling native VLAN %s on interface %s', vlan, interface)
        self._run_shell('sudo ovs-vsctl set port %s tag=%s' % (interface, vlan))

    def set_trunk_vlan(self, interface, vlans):
        """Takes an array of VLANs and sets them as trunk VLANs for the port on OVS bridge"""
        self._logger.info('Enabling trunk VLANs %s on interface %s', vlans, interface)
        vlan_str = ",".join(str(vlan) for vlan in vlans)
        self._run_shell('sudo ovs-vsctl set port %s trunks=%s' % (interface, vlan_str))

    def create_faux_device(self, index):
        """Creates faux docker container daq-faux-<index>"""
        self._run_shell('sudo cmd/faux %s' % index)
        iface = 'faux-eth0'
        prefix = int(index / 256) + 1
        suffix = index % 256
        ip_addr = '192.168.%s.%s' % (prefix, suffix)
        gateway = '192.168.1.0'
        container = 'daq-faux-%s' % index

        self._run_shell('ip addr flush %s' % iface, docker_container=container)
        self._run_shell('ip addr add %s/16 dev %s' % (ip_addr, iface), docker_container=container)
        self._run_shell('ip route add default via %s' % gateway, docker_container=container)
