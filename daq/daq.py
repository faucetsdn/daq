#!/usr/bin/env python

"""Device Automated Qualification testing framework"""

import logging
import os
import time

from mininet import log as minilog
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, Host
from mininet.cli import CLI

from tests.faucet_mininet_test_host import MakeFaucetDockerHost
from tests.faucet_mininet_test_topo import FaucetHostCleanup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DAQHost(FaucetHostCleanup, Host):
    """Base Mininet Host class, for Mininet-based tests."""

    pass


class DAQRunner():
    net = None
    switch = None

    def addHost(self, name, cls=DAQHost, ip=None, env_vars=[]):
        tmpdir = 'inst/'
        params = { 'ip': ip } if ip else {}
        params['tmpdir'] = tmpdir
        params['env_vars'] = env_vars
        host = self.net.addHost(name, cls, **params)
        link = self.net.addLink(self.switch, host, fast=False)
        if self.net.built:
            host.configDefault()
            self.switch.attach(link.intf1.name)
        return host

    def stopHost(self, host):
        logging.debug("Stopping host " + host.name)
        host.terminate()

    def pingTest(self, a, b):
        logging.debug("Ping test %s->%s" % (a.name, b.name))
        failure="ping FAILED"
        assert b.IP() != "0.0.0.0", "IP address not assigned, can't ping"
        output = a.cmd('ping -c1', b.IP(), '> /dev/null 2>&1 || echo ', failure).strip()
        if output:
            print output
        return output.strip() != failure

    def createNetwork(self):
        logging.debug("Creating miniet...")
        self.net = Mininet()

        logging.debug("Adding switch...")
        self.switch = self.net.addSwitch('s1', cls=OVSSwitch)

        logging.debug("Starting faucet container...")
        self.switch.cmd('cmd/faucet')

        targetIp = "127.0.0.1"
        logging.debug("Adding controller at %s" % targetIp)
        c1 = self.net.addController( 'c1', controller=RemoteController, ip=targetIp, port=6633 )

        logging.debug("Adding hosts...")
        h1 = self.addHost('h1', cls=MakeFaucetDockerHost('daq/networking'))
        h2 = self.addHost('h2', cls=MakeFaucetDockerHost('daq/fauxdevice'), ip="0.0.0.0")
        h3 = self.addHost('h3', cls=MakeFaucetDockerHost('daq/default'))

        logging.debug("Starting mininet...")
        self.net.start()

        logging.debug("Activating hosts...")
        h1.activate()
        h2.activate()
        h3.activate()

        logging.debug("Waiting for system to settle...")
        time.sleep(3)

        self.pingTest(h1, h3)
        self.pingTest(h3, h1)

        if self.pingTest(h2, h1):
            print "Unexpected success??!?!"
        else:
            print "(Expected failure)"

        logging.debug("Waiting for dhcp...")
        time.sleep(5)

        self.pingTest(h2, h1)

        logging.debug("Creating/activating test_ping")
        env_vars = [ "TARGET_HOST=" + h1.IP() ]
        h4 = self.addHost('h4', cls=MakeFaucetDockerHost('daq/test_ping'), env_vars = env_vars)
        h4.activate()

        CLI(self.net)

        logging.debug("Stopping faucet...")
        self.switch.cmd('docker kill daq-faucet')
        logging.debug("Stopping mininet...")
        self.net.stop()


if __name__ == '__main__':
    minilog.setLogLevel('info')
    if os.getuid() == 0:
        DAQRunner().createNetwork()
    else:
        logger.debug("You are NOT root")
