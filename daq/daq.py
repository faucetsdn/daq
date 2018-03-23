#!/usr/bin/env python

"""Device Automated Qualification testing framework"""

import logging
import os
import re
import subprocess
import time

from mininet import log as minilog
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, Host
from mininet.cli import CLI
from mininet.util import pmonitor

from tests.faucet_mininet_test_host import MakeFaucetDockerHost
from tests.faucet_mininet_test_topo import FaucetHostCleanup
from tests import faucet_mininet_test_util

from faucet_event_client import FaucetEventClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DAQHost(FaucetHostCleanup, Host):
    """Base Mininet Host class, for Mininet-based tests."""

    pass


class DAQRunner():

    DHCP_PATTERN = '> ([0-9.]+).68: BOOTP/DHCP, Reply'

    net = None
    switch = None
    target_host = None

    def addHost(self, name, cls=DAQHost, ip=None, env_vars=[]):
        tmpdir = 'inst/'
        params = { 'ip': ip } if ip else {}
        params['tmpdir'] = tmpdir
        params['env_vars'] = env_vars
        host = self.net.addHost(name, cls, **params)
        host.switch_link = self.net.addLink(self.switch, host, fast=False)
        if self.net.built:
            host.configDefault()
            intf = host.switch_link.intf1
            self.switch.attach(intf)
            # This really should be done in attach, but currently only automatic on switch startup.
            self.switch.vsctl(self.switch.intfOpts(intf))
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

    def dockerTest(self, image):
        container_name = image.split('/')[-1]
        env_vars = [ "TARGET_HOST=" + self.target_host ]
        host = self.addHost(container_name, cls=MakeFaucetDockerHost(image), env_vars = env_vars)
        host.activate()
        error_code = host.check_result()
        if error_code != 0:
            logging.info("FAILED test %s with error %s" % (image, error_code))
        else:
            logging.info("PASSED test %s" % image)

    def tcpdump_helper(self, tcpdump_host, tcpdump_filter, funcs=None,
                       vflags='-v', timeout=10, packets=2, root_intf=False,
                       intf=None):
        intf_name = (intf if intf else tcpdump_host.intf()).name
        if root_intf:
            intf_name = intf_name.split('.')[0]
        tcpdump_cmd = faucet_mininet_test_util.timeout_soft_cmd(
            'tcpdump -i %s -e -n -U %s -c %u %s' % (
                intf_name, vflags, packets, tcpdump_filter),
            timeout)
        tcpdump_out = tcpdump_host.popen(
            tcpdump_cmd,
            stdin=faucet_mininet_test_util.DEVNULL,
            stderr=subprocess.STDOUT,
            close_fds=True)
        popens = {tcpdump_host: tcpdump_out}
        tcpdump_started = False
        tcpdump_lines = []
        for host, line in pmonitor(popens):
            if host == tcpdump_host:
                tcpdump_lines += [line]
                if not tcpdump_started and re.search('listening on %s' % intf_name, line):
                    tcpdump_started = True
                    tcpdump_lines = []
                    # when we see tcpdump start, then call provided functions.
                    if funcs is not None:
                        for func in funcs:
                            func()
        assert tcpdump_started, 'tcpdump did not start: %s' % tcpdump_lines
        return tcpdump_lines


    def createNetwork(self):
        logging.debug("Creating miniet...")
        self.net = Mininet()

        logging.debug("Adding switch...")
        self.switch = self.net.addSwitch('s1', cls=OVSSwitch)

        logging.debug("Starting faucet...")
        self.switch.cmd('cmd/faucet')

        self.faucet_events = FaucetEventClient()
        self.faucet_events.connect(os.getenv('FAUCET_EVENT_SOCK'))

        targetIp = "127.0.0.1"
        logging.debug("Adding controller at %s" % targetIp)
        c1 = self.net.addController( 'c1', controller=RemoteController, ip=targetIp, port=6633 )

        logging.debug("Adding hosts...")
        h1 = self.addHost('h1', cls=MakeFaucetDockerHost('daq/networking'))
        h3 = self.addHost('h3')

        logging.debug("Starting mininet...")
        self.net.start()

        logging.debug("Activating networking...")
        h1.activate()

        logging.debug("Waiting for system to settle...")
        time.sleep(3)

        logging.debug("Adding fauxdevice...")
        h2 = self.addHost('h2', cls=MakeFaucetDockerHost('daq/fauxdevice'), ip="0.0.0.0")

        self.pingTest(h1, h3)
        self.pingTest(h3, h1)

        assert not self.pingTest(h2, h1), "Unexpected success??!?!"
        print "(Expected failure)"

        h2.activate()

        target_port = self.switch.ports[h2.switch_link.intf1]
        logging.debug("Monitoring faucet event socket for target port add %d..." % target_port)
        for event in self.faucet_events.next_event():
            if self.faucet_events.is_port_active_event(event) == target_port:
                break

        logging.debug("Waiting for dhcp response on %s" % h1.switch_link.intf1)
        filter="src port 67"
        dhcp_lines = self.tcpdump_helper(self.switch, filter, intf=h1.switch_link.intf1, vflags='', packets=1, timeout=60)
        self.target_host = re.search(self.DHCP_PATTERN, dhcp_lines[0]).group(1)
        logging.debug('Host %s is at %s' % (h2.name, self.target_host))
        h2.setIP(self.target_host)

        self.pingTest(h2, h1)
        self.pingTest(h1, h2)

        self.dockerTest('daq/test_ping')
        self.dockerTest('daq/test_nmap')
        self.dockerTest('daq/test_pass')
        self.dockerTest('daq/test_fail')

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
