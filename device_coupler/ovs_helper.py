"""Module to help setup OVS bridges, VxLANs and other virt network components"""

from __future__ import absolute_import, division

from functools import partial
from python_lib.shell_command_helper import ShellCommandHelper
from device_coupler.utils import get_logger

import re


class OvsHelper:
    """Class to build OVS bridges, VxLANs and other network components"""
    DEFAULT_VXLAN_PORT = 4789
    VXLAN_CMD_FMT = 'ip link add %s type vxlan id %s remote %s dstport %s srcport %s %s nolearning'

    def __init__(self):
        self._logger = get_logger('OvsHelper')
        self._run_shell = partial(ShellCommandHelper().run_cmd, capture=True)
        self._run_shell_no_raise = partial(ShellCommandHelper().run_cmd, capture=True, strict=False)

    def _set_interface_up(self, interface, raise_exc=True):
        shell_fn = self._run_shell if raise_exc else self._run_shell_no_raise
        shell_fn('sudo ip link set %s up' % interface)

    def _set_interface_down(self, interface, raise_exc=True):
        shell_fn = self._run_shell if raise_exc else self._run_shell_no_raise
        shell_fn('sudo ip link set %s down' % interface)

    def create_vxlan_endpoint(self, interface, remote_ip, vni, local_vtep_ip=None):
        """Creates a VxLAN endpoint"""
        self._logger.info("Creating VxLAN endpoint %s ip: %s vni: %s local vtep ip: %s",
                          interface, remote_ip, vni, local_vtep_ip)
        vxlan_cmd = 'sudo ' + self.VXLAN_CMD_FMT % (
            interface, vni, remote_ip, self.DEFAULT_VXLAN_PORT,
            self.DEFAULT_VXLAN_PORT, self.DEFAULT_VXLAN_PORT)
        self._logger.info('Executing VXLAN cmd: %s', vxlan_cmd)
        self._run_shell(vxlan_cmd)
        if local_vtep_ip:
            self._add_ip_address(local_vtep_ip, interface)
        self._set_interface_up(interface)
        return interface

    def _add_ip_address(self, interface, ip_address, netmask=24):
        self._run_shell('sudo ip addr add %s/%s dev %s' % (ip_address, netmask, interface))

    def remove_vxlan_endpoint(self, interface, bridge):
        """Clears VxLAN endpoint"""
        self._logger.info('Removing vxlan interface %s', interface)
        self._run_shell_no_raise('sudo ip link set %s down' % interface)
        self._set_interface_down(interface, raise_exc=False)
        self._run_shell_no_raise('sudo ip link del %s' % interface)
        self._run_shell_no_raise('sudo ovs-vsctl del-port %s %s' % (bridge, interface))

    def create_ovs_bridge(self, name):
        """Creates OVS bridge"""
        self._logger.info('Creating OVS bridge %s', name)
        self._run_shell(
            'sudo ovs-vsctl add-br %s -- set bridge %s other-config:forward-bpdu=true'
            % (name, name))

    def delete_ovs_bridge(self, name):
        """Delete ovs bridge"""
        self._logger.info('Deleting OVS bridge %s', name)
        self._run_shell_no_raise('sudo ovs-vsctl del-br %s' % name)

    def add_iface_to_bridge(self, bridge, iface, tag=None, trunks=None):
        """Add interface to OVS bridge"""
        self._logger.info('Adding interface %s to bridge %s tag %s trunk %s',
                          iface, bridge, tag, trunks)
        assert not (tag and trunks), 'Can\'t enable both tag and trunks'
        cmd = 'sudo ovs-vsctl add-port %s %s' % (bridge, iface)
        if tag:
            cmd = cmd + ' tag=%s' % tag
        if trunks:
            cmd = cmd + ' trunks=%s' % trunks
        self._run_shell(cmd)

    def set_native_vlan(self, interface, vlan):
        """Set native VLAN to port on OVS bridge"""
        self._logger.info('Enabling native VLAN %s on interface %s', vlan, interface)
        self._run_shell('sudo ovs-vsctl set port %s tag=%s' % (interface, vlan))

    def set_trunk_vlan(self, interface, vlans):
        """Takes an array of VLANs and sets them as trunk VLANs for the port on OVS bridge"""
        self._logger.info('Enabling trunk VLANs %s on interface %s', vlans, interface)
        vlan_str = ",".join(str(vlan) for vlan in vlans)
        self._run_shell('sudo ovs-vsctl set port %s trunks=%s' % (interface, vlan_str))

    def create_veth_pair(self, iface1, iface2):
        """Creates a veth pair with interface names iface1, iface2"""
        self._run_shell('sudo ip link add dev %s type veth peer name %s' % (iface1, iface2))
        self._set_interface_up(iface1)
        self._set_interface_up(iface2)

    def get_interface_ofport(self, iface):
        """Returns ofport number of interface from ovs table"""
        _, out, _ = self._run_shell('ovs-vsctl get Interface %s ofport' % iface)
        return int(out.strip())

    def get_forwarding_table(self, bridge):
        """Returns forwarding table of given OVS bridge in the form [(<port>, <vlan>, <mac>)]"""
        _, out, _ = self._run_shell('ovs-appctl fdb/show %s' % bridge)
        return self._filter_forwarding_table(out)

    def _filter_forwarding_table(self, table):
        """Converts fdb table string to list[(<port>, <vlan>, <mac>)]"""
        filtered_table = re.findall(r"\d{1,4}\s+\d{1,4}\s+(?:[0-9a-fA-F]:?){12}", table)
        return [tuple(entry.split()) for entry in filtered_table]

    def get_interface_ip(self, iface="eth0"):
        """Returns IP of given interface"""
        try:
            retcode, out_str, stderr = self._run_shell('ip addr show %s' % iface)
        except Exception:
            self._logger.error('Error while executing command: %s', stderr)
            return None
        return re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', out_str).group(0)
