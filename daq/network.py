"""Networking module"""

import logging
import os

import topology

from mininet import node as mininet_node
from mininet import net as mininet_net
from mininet import link as mininet_link
from mininet import cli as mininet_cli
from clib import mininet_test_topo

LOGGER = logging.getLogger('network')

class DAQHost(mininet_test_topo.FaucetHostCleanup, mininet_node.Host):
    """Base Mininet Host class, for Mininet-based tests."""
    # pylint: disable=too-few-public-methods
    pass


class DummyNode():
    """Dummy node used to handle shadow devices"""
    # pylint: disable=invalid-name
    def addIntf(self, node, port=None):
        """No-op for adding an interface"""
        pass

    def cmd(self, cmd, *args, **kwargs):
        """No-op for running a command"""
        pass


class TestNetwork():
    """Test network manager"""

    OVS_CLS = mininet_node.OVSSwitch
    MAX_INTERNAL_DPID = 100

    def __init__(self, config):
        self.config = config
        self.net = None
        self.pri = None
        self.sec = None
        self.sec_dpid = None
        self.sec_port = None
        self.ext_intf = None
        self.switch_links = {}
        self.topology = None

    # pylint: disable=too-many-arguments
    def add_host(self, name, cls=DAQHost, ip_addr=None, env_vars=None, vol_maps=None,
                 port=None, tmpdir=None):
        """Add a host to the ecosystem"""
        params = {'ip': ip_addr} if ip_addr else {}
        params['tmpdir'] = os.path.join(tmpdir, 'nodes') if tmpdir else None
        params['env_vars'] = env_vars if env_vars else []
        params['vol_maps'] = vol_maps if vol_maps else []
        host = self.net.addHost(name, cls, **params)
        try:
            LOGGER.debug('Created host %s with pid %s/%s', name, host.pid, host.shell.pid)
            switch_link = self.net.addLink(self.pri, host, port1=port, fast=False)
            self.switch_links[host] = switch_link
            if self.net.built:
                host.configDefault()
                self._switch_attach(self.pri, switch_link.intf1)
        except:
            host.terminate()
            raise
        return host

    def get_host_interface(self, host):
        """Get the internal link interface for this host"""
        return self.switch_links[host].intf2

    def _switch_attach(self, switch, intf):
        switch.attach(intf)
        # This really should be done in attach, but currently only automatic on switch startup.
        switch.vsctl(switch.intfOpts(intf))

    def _switch_del_intf(self, switch, intf):
        del switch.intfs[switch.ports[intf]]
        del switch.ports[intf]
        del switch.nameToIntf[intf.name]

    def remove_host(self, host):
        """Remove a host from the ecosystem"""
        index = self.net.hosts.index(host)
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

    def _create_secondary(self):
        self.sec_dpid = self.topology.get_sec_dpid()
        self.sec_port = self.topology.get_sec_port()
        self.ext_intf = self.topology.get_sec_intf()
        if self.ext_intf:
            LOGGER.info('Configuring external secondary with dpid %s on intf %s',
                        self.sec_dpid, self.ext_intf)
            sec_intf = mininet_link.Intf(self.ext_intf, node=DummyNode(), port=1)
            self.pri.addIntf(sec_intf, port=1)
        else:
            LOGGER.info('Creating ovs sec with dpid/port %s/%d', self.sec_dpid, self.sec_port)
            self.sec = self.net.addSwitch('sec', dpid=str(self.sec_dpid), cls=self.OVS_CLS)

            link = self.net.addLink(self.pri, self.sec, port1=1,
                                    port2=self.sec_port, fast=False)
            LOGGER.info('Added switch link %s <-> %s', link.intf1.name, link.intf2.name)
            self.ext_intf = link.intf1.name
            self._attach_sec_device_links()

    def _is_dpid_external(self, dpid):
        return int(dpid) > self.MAX_INTERNAL_DPID

    def _attach_sec_device_links(self):
        topology_intfs = self.topology.get_device_intfs()
        for topology_intf in topology_intfs:
            intf_name = topology_intf['name']
            intf_port = topology_intf['port']
            LOGGER.info("Attaching device interface %s on port %d.", intf_name, intf_port)
            intf = mininet_link.Intf(intf_name, node=DummyNode(), port=intf_port)
            intf.port = intf_port
            self.sec.addIntf(intf, port=intf_port)
            self._switch_attach(self.sec, intf)

    def is_device_port(self, dpid, port):
        """Check if the dpid/port combo is for a valid device"""
        target_dpid = int(self.sec_dpid)
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
        self.net = mininet_net.Mininet()

        LOGGER.debug("Adding primary...")
        self.pri = self.net.addSwitch('pri', dpid='1', cls=self.OVS_CLS)

        LOGGER.info("Activating faucet topology...")
        self.topology = topology.FaucetTopology(self.config, self.pri)
        self.topology.initialize()
        self.topology.start()

        target_ip = "127.0.0.1"
        LOGGER.debug("Adding controller at %s", target_ip)
        controller = mininet_node.RemoteController
        self.net.addController('controller', controller=controller, ip=target_ip, port=6633)

        LOGGER.debug("Adding secondary...")
        self._create_secondary()

        LOGGER.info("Starting mininet...")
        self.net.start()

    def direct_port_traffic(self, target_mac, target):
        """Direct traffic for a given mac to target port"""
        port = target['port'] if target else None
        LOGGER.info('Directing port traffic for %s to %s', target_mac, port)
        self.topology.direct_port_traffic(target_mac, target)

    def device_group_for(self, target_mac):
        """Find the target device group for the given address"""
        return self.topology.device_group_for(target_mac)
