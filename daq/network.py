"""Networking module"""

from __future__ import absolute_import

from ipaddress import ip_network
import copy
from functools import partial
import os
import time
import yaml

import logger
from topology import FaucetTopology
from env import DAQ_RUN_DIR

from mininet import node as mininet_node
from mininet import net as mininet_net
from mininet import link as mininet_link
from mininet import cli as mininet_cli
from mininet import util as mininet_util
from forch import faucetizer
from forch.proto.forch_configuration_pb2 import OrchestrationConfig

LOGGER = logger.get_logger('network')


NATIVE_GATEWAY_INTF = 'pri-eth1'
NATIVE_NET_PREFIX = '10.21'


# pylint: disable=too-few-public-methods
class DAQHost(mininet_node.Host):
    """Base Mininet Host class, for Mininet-based tests."""


class FakeNode:
    """Fake node used to handle shadow devices"""
    # pylint: disable=invalid-name
    def addIntf(self, node, port=None):
        """No-op for adding an interface"""

    def cmd(self, cmd, *args, **kwargs):
        """No-op for running a command"""


class TestNetwork:
    """Test network manager"""

    OVS_CLS = mininet_node.OVSSwitch
    MAX_INTERNAL_DPID = 100
    DEFAULT_FAUCET_OF_PORT = 6653
    DEFAULT_GAUGE_OF_PORT = 6654
    DEFAULT_MININET_SUBNET = "10.20.0.0/16"
    INTERMEDIATE_FAUCET_FILE = os.path.join(DAQ_RUN_DIR, "faucet_intermediate.yaml")
    INTERMEDIATE_GAUGE_FILE = os.path.join(DAQ_RUN_DIR, "gauge.yaml")
    OUTPUT_FAUCET_FILE = os.path.join(DAQ_RUN_DIR, "faucet.yaml")
    _CTRL_PRI_IFACE = 'ctrl-pri'
    _DEFAULT_VXLAN_PORT = 4789
    _VXLAN_CMD_FMT = 'ip link add %s type vxlan id %s remote %s dstport %s srcport %s %s nolearning'

    def __init__(self, config):
        self.config = config
        self.net = None
        self.pri = None
        self.sec = None
        self.sec_dpid = None
        self.sec_port = None
        self.tap_intf = None
        self._settle_sec = int(config.get('settle_sec', 0))
        subnet = config.get('internal_subnet', {}).get('subnet', self.DEFAULT_MININET_SUBNET)
        self._mininet_subnet = ip_network(subnet)
        self._used_ip_indices = set()
        self.topology = FaucetTopology(self.config)
        switch_setup = config.get('switch_setup', {})
        self.ext_intf = switch_setup.get('data_intf')
        self.ext_mac = switch_setup.get('data_mac')
        self.ext_faucet_ofpt = int(switch_setup.get('lo_port', self.DEFAULT_FAUCET_OF_PORT))
        self.ext_gauge_ofpt = int(switch_setup.get('lo_port_2', self.DEFAULT_GAUGE_OF_PORT))
        self.ext_loip = switch_setup.get('mods_addr')
        self.switch_links = {}
        orch_config = OrchestrationConfig()
        self.faucitizer = faucetizer.Faucetizer(
            orch_config, self.INTERMEDIATE_FAUCET_FILE, self.OUTPUT_FAUCET_FILE)
        self._vxlan_port_sets = set()

    # pylint: disable=too-many-arguments
    def add_host(self, name, cls=DAQHost, ip_addr=None, env_vars=None, vol_maps=None,
                 port=None, tmpdir=None):
        """Add a host to the ecosystem"""
        override_ip = bool(ip_addr)
        if self._used_ip_indices and not ip_addr:
            for index in range(1, max(self._used_ip_indices)):
                if index not in self._used_ip_indices:
                    prefix_length = self._mininet_subnet.prefixlen
                    ip_addr = '%s/%s' % (mininet_util.ipAdd(index, prefixLen=prefix_length,
                                                            ipBaseNum=self.net.ipBaseNum),
                                         prefix_length)
                    break
        params = {'ip': ip_addr} if ip_addr else {}
        params['tmpdir'] = os.path.join(tmpdir, 'nodes') if tmpdir else None
        params['env_vars'] = env_vars if env_vars else []
        params['vol_maps'] = vol_maps if vol_maps else []
        try:
            host = self._retry_func(partial(self.net.addHost, name, cls, **params))
        except Exception as e:
            # If addHost fails, ip allocation needs to be explicityly cleaned up.
            self._reset_mininet_next_ip()
            raise e
        try:
            switch_link = self._retry_func(
                partial(self.net.addLink, self.pri, host, port1=port, fast=False))
            LOGGER.info('Created host %s with pid %s/%s, intf %s',
                        name, host.pid, host.shell.pid, switch_link.intf1)
            host.switch_intf = switch_link.intf1
            self.switch_links[host] = switch_link
            if self.net.built:
                host.configDefault()
                self._switch_attach(self.pri, host.switch_intf)
        except Exception as e:
            host.terminate()
            raise e

        if not override_ip and host.IP():
            self._used_ip_indices.add(self._get_host_ip_index(host))
        return host

    def _retry_func(self, func):
        retries = 3
        for retry in range(1, retries + 1):
            try:
                return func()
            except Exception as e:
                LOGGER.error('Caught exception on try %s: %s', retry, repr(e))
                if retry is retries:
                    raise e
            time.sleep(1)
        raise Exception('unknown')

    def get_host_interface(self, host):
        """Get the internal link interface for this host"""
        return self.switch_links[host].intf2

    def _switch_attach(self, switch, intf):
        self._retry_func(partial(switch.attach, intf))
        # This really should be done in attach, but currently only automatic on switch startup.
        switch.vsctl(switch.intfOpts(intf))

    def _switch_del_intf(self, switch, intf):
        del switch.intfs[switch.ports[intf]]
        del switch.ports[intf]
        del switch.nameToIntf[intf.name]

    def _reset_mininet_next_ip(self):
        # Resets Mininet's next ip so subnet ips don't run out.
        # IP overrides are excluded from this set.
        self.net.nextIP = max(self._used_ip_indices or [0]) + 1

    def remove_host(self, host):
        """Remove a host from the ecosystem"""
        index = self.net.hosts.index(host)
        if host.IP() and self._get_host_ip_index(host) in self._used_ip_indices:
            self._used_ip_indices.remove(self._get_host_ip_index(host))
            self._reset_mininet_next_ip()
        if index:
            del self.net.hosts[index]
        if host in self.switch_links:
            switch_link = self.switch_links[host]
            del self.switch_links[host]
            intf = switch_link.intf1
            self.pri.detach(intf)
            self._switch_del_intf(self.pri, intf)
            intf.delete()
            del self.net.links[self.net.links.index(switch_link)]

    def get_subnet(self):
        """Gets the internal mininet subnet"""
        return copy.copy(self._mininet_subnet)

    def _link_secondary(self, sec_intf):
        self.pri.addIntf(sec_intf, port=self.topology.PRI_TRUNK_PORT)

    def _create_secondary(self):
        self.sec_dpid = self.topology.get_sec_dpid()
        self.sec_port = self.topology.get_sec_port()
        vxlan_taps = self.config.get('device_reporting', {}).get('server_port')

        if self.ext_intf:
            LOGGER.info('Configuring external secondary with dpid %s on intf %s',
                        self.sec_dpid, self.ext_intf)
            sec_intf = mininet_link.Intf(self.ext_intf, node=FakeNode(), port=1)
            self._link_secondary(sec_intf)
            self.tap_intf = self.ext_intf
        elif vxlan_taps:
            LOGGER.info('Creating ovs sec with dpid %s for vxlan taps',
                        self.topology.VXLAN_SEC_DPID)
            self.sec = self.net.addSwitch('sec', dpid=str(self.topology.VXLAN_SEC_DPID),
                                          cls=self.OVS_CLS)
            link = self._retry_func(partial(self.net.addLink, self.pri, self.sec,
                                            port1=self.topology.PRI_TRUNK_PORT,
                                            port2=self.topology.VXLAN_SEC_TRUNK_PORT, fast=False))
            LOGGER.info('Added switch link %s <-> %s', link.intf1.name, link.intf2.name)
            self.tap_intf = link.intf1.name
        else:
            LOGGER.info('Creating ovs sec with dpid/port %s/%d', self.sec_dpid, self.sec_port)
            self.sec = self.net.addSwitch('sec', dpid=str(self.sec_dpid), cls=self.OVS_CLS)

            link = self._retry_func(partial(self.net.addLink, self.pri, self.sec, port1=1,
                                            port2=self.sec_port, fast=False))
            LOGGER.info('Added switch link %s <-> %s', link.intf1.name, link.intf2.name)
            self._attach_sec_device_links()

    def _is_dpid_external(self, dpid):
        return int(dpid) > self.MAX_INTERNAL_DPID

    def _attach_sec_device_links(self):
        topology_intfs = self.topology.get_device_intfs()
        for intf_port in range(1, len(topology_intfs) + 1):
            intf_name = topology_intfs[intf_port-1]
            LOGGER.info("Attaching device interface %s on port %d.", intf_name, intf_port)
            intf = mininet_link.Intf(intf_name, node=FakeNode(), port=intf_port)
            intf.port = intf_port
            self.sec.addIntf(intf, port=intf_port)
            self._switch_attach(self.sec, intf)

    def _get_host_ip_index(self, host):
        """Returns the ip index within the mininet subnet."""
        return mininet_util.ipParse(host.IP()) - self.net.ipBaseNum

    def is_system_port(self, dpid, port):
        """Check if the dpid/port combo is the system trunk port"""
        return dpid == self.topology.PRI_DPID and port == self.topology.PRI_TRUNK_PORT

    def is_device_port(self, dpid, port):
        """Check if the dpid/port combo is for a valid device"""
        target_dpid = int(self.sec_dpid) if self.sec_dpid else None
        return dpid == target_dpid and port < self.sec_port

    def cli(self):
        """Drop into the mininet CLI"""
        mininet_cli.CLI(self.net)

    def stop(self):
        """Stop network"""
        self.topology.stop()
        self.net.stop()

    def initialize(self):
        """Initialize network"""

        LOGGER.debug("Creating miniet...")
        self.net = mininet_net.Mininet(ipBase=str(self._mininet_subnet))

        LOGGER.debug("Adding primary...")
        self.pri = self.net.addSwitch('pri', dpid=str(self.topology.PRI_DPID), cls=self.OVS_CLS)

        LOGGER.info("Initializing topology and faucitizer...")
        self.topology.initialize(self.pri)
        self._generate_behavioral_config()

        LOGGER.info("Activating faucet topology...")
        self.topology.start()

        target_ip = "127.0.0.1"
        LOGGER.debug("Adding controller at %s", target_ip)
        controller = mininet_node.RemoteController
        self.net.addController('faucet', controller=controller,
                               ip=target_ip, port=self.ext_faucet_ofpt)
        self.net.addController('gauge', controller=controller,
                               ip=target_ip, port=self.ext_gauge_ofpt)

    def activate(self, native_gateway=None):
        """Activate the network"""

        if native_gateway:
            gateway_intf = str(native_gateway.host.switch_intf)
            LOGGER.info('Setting native gateway %s on %s', native_gateway,
                        gateway_intf)
            self._link_secondary(native_gateway.host.switch_intf)
        else:
            LOGGER.debug("Adding secondary...")
            self._create_secondary()

        LOGGER.info("Starting mininet...")
        self.net.start()

        if self.ext_loip:
            self._attach_switch_interface(self._CTRL_PRI_IFACE)

        if native_gateway:
            # Native gateway is initialized prior to mininet start
            # which caused the mininet host to have no IP
            self._used_ip_indices.add(self._get_host_ip_index(native_gateway.host))

        if native_gateway:
            self.tap_intf = NATIVE_GATEWAY_INTF

    def _configure_remote_tap(self, device):
        """Configure the tap for remote connection"""
        if not device.session_endpoint or self.ext_intf or device.port.vxlan:
            return
        remote = device.session_endpoint
        vxlan_config = self.config.get('switch_setup', {}).get('endpoint', {})
        vxlan_port = self.topology.VXLAN_SEC_TRUNK_PORT + 1
        while vxlan_port in self._vxlan_port_sets:
            vxlan_port += 1
        self._cleanup_remote_tap(device, vxlan_port=vxlan_port)
        self._vxlan_port_sets.add(vxlan_port)
        device.port.vxlan = vxlan_port
        interface = "vxlan" + str(vxlan_port)
        dst_port = remote.port or self._DEFAULT_VXLAN_PORT
        src_port = int(vxlan_config.get('port', self._DEFAULT_VXLAN_PORT))
        vxlan_cmd = self._VXLAN_CMD_FMT % (interface, remote.vni, remote.ip,
                                           dst_port, src_port, dst_port)
        LOGGER.info('Configuring interface %s: %s', device.mac, vxlan_cmd)
        self.sec.cmd(vxlan_cmd)
        self.sec.cmd('ip link set %s up' % interface)
        self.sec.vsctl('add-port', self.sec.name, interface, '--',
                       'set', 'interface', interface, 'ofport_request=%s' % vxlan_port)
        LOGGER.info('_configure_remote_tap Successfully configured interface %s', device.mac)

    def _cleanup_remote_tap(self, device, vxlan_port=None):
        vxlan = vxlan_port if vxlan_port else device.port.vxlan
        if not vxlan:
            return
        interface = "vxlan" + str(vxlan)
        LOGGER.info('Cleaning interface %s: %s', device.mac, interface)
        self.sec.cmd('ip link set %s down' % interface)
        self.sec.cmd('ip link del %s' % interface)
        self.sec.vsctl('del-port', self.sec.name, interface)
        self._vxlan_port_sets.discard(vxlan)
        device.port.vxlan = None

    def direct_port_traffic(self, device, port, target):
        """Direct traffic for a given mac to target port"""
        dest = target['port_set'] if target else None
        LOGGER.info('Directing traffic for %s on port %s to %s', device, port, dest)
        # TODO: Convert this to use faucitizer to change vlan
        self.topology.direct_port_traffic(device, port, target)
        self._generate_behavioral_config()

    def _generate_behavioral_config(self):
        with open(self.INTERMEDIATE_FAUCET_FILE, 'w') as file:
            network_topology = self.topology.get_network_topology()
            yaml.safe_dump(network_topology, file)

        self.faucitizer.reload_structural_config(self.INTERMEDIATE_FAUCET_FILE)

        with open(self.INTERMEDIATE_GAUGE_FILE, 'w') as file:
            yaml.safe_dump(self.topology.get_gauge_config(), file)
        self.faucitizer.reload_and_flush_gauge_config(self.INTERMEDIATE_GAUGE_FILE)

        if self._settle_sec:
            LOGGER.info('Waiting %ds for network to settle', self._settle_sec)
            time.sleep(self._settle_sec)

    def direct_device_traffic(self, device):
        """Modify gateway set's vlan to match triggering vlan"""
        port_set = device.gateway.port_set if device.gateway else None
        LOGGER.info('Directing traffic for %s on %s/%s/%s to %s',
                    device.mac, device.vlan, device.assigned, device.port.vxlan, port_set)
        # TODO: Convert this to use faucitizer to change vlan
        self.topology.direct_device_traffic(device)
        self._generate_behavioral_config()
        if port_set:
            self._configure_remote_tap(device)
        else:
            self._cleanup_remote_tap(device)

    def _attach_switch_interface(self, switch_intf_name):
        switch_port = self.topology.switch_port()
        LOGGER.info('Attaching switch interface %s on port %s', switch_intf_name, switch_port)
        self.pri.vsctl('add-port', self.pri.name, switch_intf_name, '--',
                       'set', 'interface', switch_intf_name, 'ofport_request=%s' % switch_port)

    def delete_mirror_interface(self, port):
        """Delete a mirroring interface on the given port"""
        return self.create_mirror_interface(port, delete=True)

    def create_mirror_interface(self, port, delete=False):
        """Create/delete a mirror interface for the given port"""
        mirror_intf_name = self.topology.mirror_iface_name(port)
        mirror_intf_peer = mirror_intf_name + '-ext'
        mirror_port = self.topology.mirror_port(port)
        if delete:
            LOGGER.info('Deleting mirror pair %s <-> %s', mirror_intf_name, mirror_intf_peer)
            self.pri.cmd('ip link del %s' % mirror_intf_name)
        else:
            LOGGER.info('Creating mirror pair %s <-> %s at %d',
                        mirror_intf_name, mirror_intf_peer, mirror_port)
            mininet_util.makeIntfPair(mirror_intf_name, mirror_intf_peer)
            self.pri.cmd('ip link set %s up' % mirror_intf_name)
            self.pri.cmd('ip link set %s up' % mirror_intf_peer)
            self.pri.vsctl('add-port', self.pri.name, mirror_intf_name, '--',
                           'set', 'interface', mirror_intf_name, 'ofport_request=%s' % mirror_port)
        return mirror_intf_name

    def device_group_for(self, device):
        """Find the target device group for the given device."""
        return self.topology.device_group_for(device)

    def device_group_size(self, group_name):
        """Return the size of the given group."""
        return self.topology.device_group_size(group_name)
