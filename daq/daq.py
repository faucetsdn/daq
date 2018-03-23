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

from pipe_monitor import PipeMonitor

from tests.faucet_mininet_test_host import MakeFaucetDockerHost
from tests.faucet_mininet_test_topo import FaucetHostCleanup
from tests import faucet_mininet_test_util

from faucet_event_client import FaucetEventClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DAQHost(FaucetHostCleanup, Host):
    """Base Mininet Host class, for Mininet-based tests."""

    pass


class TcpMonitor():

    pipe = None
    tcpdump_started = False
    last_line = None
    funcs = None

    def __init__(self, tcpdump_host, tcpdump_filter, funcs=None,
                 vflags='-v', duration_sec=10, packets=2, root_intf=False):
        self.intf_name = tcpdump_host.intf().name
        self.funcs = funcs
        if root_intf:
            self.intf_name = self.intf_name.split('.')[0]
        tcpdump_cmd = faucet_mininet_test_util.timeout_soft_cmd(
            'tcpdump -i %s -e -n -U %s -c %u %s' % (
                self.intf_name, vflags, packets, tcpdump_filter),
            duration_sec)
        self.pipe = tcpdump_host.popen(
            tcpdump_cmd,
            stdin=faucet_mininet_test_util.DEVNULL,
            stderr=subprocess.STDOUT,
            close_fds=True)

    def stream(self):
        return self.pipe.stdout

    def next_line(self):
        line = self.pipe.stdout.readline()
        assert len(line) > 0 or self.tcpdump_started, 'tcpdump did not start: %s' % self.last_line
        if self.tcpdump_started:
            return line
        elif re.search('listening on %s' % self.intf_name, line):
            self.tcpdump_started = True
            # when we see tcpdump start, then call provided functions.
            if self.funcs is not None:
                for func in self.funcs:
                    func()
        else:
            self.last_line = line


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
        logging.debug("Expected failure observed.")

        monitor = PipeMonitor(timeout_ms=1000)

        target_port = self.switch.ports[h2.switch_link.intf1]
        logging.debug("Monitoring faucet event socket for target port add %d" % target_port)
        monitor.add_pipe(self.faucet_events.sock)

        logging.debug("Monitoring dhcp responses from %s" % h1.name)
        filter="src port 67"
        dhcp_monitor = TcpMonitor(h1, filter, vflags='', packets=1, duration_sec=60)
        monitor.add_pipe(dhcp_monitor.stream())

        logging.debug("Activating target %s" % h2.name)
        h2.activate()

        for pipe in monitor.monitor_pipes():
            if pipe == self.faucet_events.sock:
                event = self.faucet_events.next_event()
                if self.faucet_events.is_port_active_event(event) == target_port:
                    logging.debug('Switch port %d active' % target_port)
                    monitor.remove_pipe(self.faucet_events.sock)
            elif pipe == dhcp_monitor.stream():
                dhcp_line = dhcp_monitor.next_line()
                if dhcp_line:
                    self.target_host = re.search(self.DHCP_PATTERN, dhcp_line).group(1)
                    logging.debug('Host %s is at %s' % (h2.name, self.target_host))
                    h2.setIP(self.target_host)
                    monitor.remove_pipe(dhcp_monitor.stream())
            elif pipe == None:
                logging.debug('Waiting for monitors to clear...')
            else:
                assert False, 'Unknown pipe %s' % pipe

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
