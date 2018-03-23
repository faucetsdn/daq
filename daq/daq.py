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


def addHost(net, switch, name, cls=DAQHost, ip=None, env_vars=[]):
    tmpdir = 'inst/'
    params = { 'ip': ip } if ip else {}
    params['tmpdir'] = tmpdir
    params['env_vars'] = env_vars
    host = net.addHost(name, cls, **params)
    link = net.addLink(switch, host, fast=False)
    if net.built:
        host.configDefault()
        switch.attach(link.intf1.name)
    return host


def stopHost():
    logging.debug("Stopping host h2")
    h2.terminate()
    time.sleep(1)


def pingTest(a, b):
    logging.debug("Ping test %s->%s" % (a.name, b.name))
    failure="ping FAILED"
    assert b.IP() != "0.0.0.0", "IP address not assigned, can't ping"
    output = a.cmd('ping -c1', b.IP(), '> /dev/null 2>&1 || echo ', failure).strip()
    if output:
        print output
    return output.strip() != failure


def createNetwork():

    logging.debug("Creating miniet...")
    net = Mininet()

    logging.debug("Adding switch...")
    switch = net.addSwitch('s1', cls=OVSSwitch)

    logging.debug("Starting faucet container...")
    switch.cmd('cmd/faucet')

    targetIp = "127.0.0.1"
    logging.debug("Adding controller at %s" % targetIp)
    c1 = net.addController( 'c1', controller=RemoteController, ip=targetIp, port=6633 )

    logging.debug("Adding hosts...")
    h1 = addHost(net, switch, 'h1', cls=MakeFaucetDockerHost('daq/networking'))
    h2 = addHost(net, switch, 'h2', cls=MakeFaucetDockerHost('daq/fauxdevice'), ip="0.0.0.0")
    h3 = addHost(net, switch, 'h3', cls=MakeFaucetDockerHost('daq/default'))

    logging.debug("Starting mininet...")
    net.start()

    h1.activate()
    h2.activate()
    h3.activate()

    logging.debug("Waiting for system to settle...")
    time.sleep(3)

    pingTest(h1, h3)
    pingTest(h3, h1)

    if pingTest(h2, h1):
        print "Unexpected success??!?!"
    else:
        print "(Expected failure)"

    logging.debug("Waiting for dhcp...")
    time.sleep(5)

    pingTest(h2, h1)

    logging.debug("Creating/activating test_ping")
    env_vars = [ "TARGET_HOST=" + h1.IP() ]
    h4 = addHost(net, switch, 'h4', cls=MakeFaucetDockerHost('daq/test_ping'), env_vars = env_vars)
    h4.activate()

    CLI(net)

    logging.debug("Stopping faucet...")
    switch.cmd('docker kill daq-faucet')
    logging.debug("Stopping mininet...")
    net.stop()


if __name__ == '__main__':
    minilog.setLogLevel('info')
    if os.getuid() != 0:
        logger.debug("You are NOT root")
    elif os.getuid() == 0:
        createNetwork()
