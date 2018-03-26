#!/usr/bin/env python

"""Device Automated Qualification testing framework"""

import logging
import os
import re
import signal
import time

from mininet import log as minilog
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, Host
from mininet.cli import CLI
from mininet.util import pmonitor

from tests.faucet_mininet_test_host import MakeFaucetDockerHost
from tests.faucet_mininet_test_topo import FaucetHostCleanup
from tests import faucet_mininet_test_util

from stream_monitor import StreamMonitor
from tcp_helper import TcpHelper
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

    def switchDelIntf(self, switch, intf):
        del switch.intfs[switch.ports[intf]]
        del switch.ports[intf]
        del switch.nameToIntf[intf.name]

    def removeHost(self, host):
        intf = host.switch_link.intf1
        self.switch.detach(intf)
        self.switchDelIntf(self.switch, intf)
        intf.delete()
        del self.net.links[self.net.links.index(host.switch_link)]
        del self.net.hosts[self.net.hosts.index(host)]

    def stopHost(self, host):
        logging.debug("Stopping host " + host.name)
        host.terminate()

    def pingTest(self, a, b):
        logging.debug("Ping test %s->%s" % (a.name, b.name))
        failure="ping FAILED"
        assert b.IP() != "0.0.0.0", "IP address not assigned, can't ping"
        output = a.cmd('ping -c2', b.IP(), '> /dev/null 2>&1 || echo ', failure).strip()
        if output:
            print output
        return output.strip() != failure

    def dockerTest(self, image):
        container_name = image.split('/')[-1]
        env_vars = [ "TARGET_HOST=" + self.target_host ]
        host = self.addHost(container_name, cls=MakeFaucetDockerHost(image), env_vars = env_vars)
        host.activate()
        error_code = host.wait()
        self.removeHost(host)
        if error_code != 0:
            logging.info("FAILED test %s with error %s" % (image, error_code))
        else:
            logging.info("PASSED test %s" % image)
        return error_code == 0

    def runner(self):
        logging.debug("Creating miniet...")
        self.net = Mininet()

        logging.debug("Adding switch...")
        self.switch = self.net.addSwitch('s1', cls=OVSSwitch)

        logging.debug("Starting faucet...")
        output = self.switch.cmd('cmd/faucet && echo SUCCESS')
        if not output.strip().endswith('SUCCESS'):
            print output
            assert False, 'Faucet startup failed'

        logging.debug("Attaching event channel...")
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

        try:
            assert self.pingTest(h1, h3)
            assert self.pingTest(h3, h1)

            assert not self.pingTest(h2, h1), "Unexpected success??!?!"
            logging.debug("Expected failure observed.")

            monitor = StreamMonitor(timeout_ms=1000)

            target_port = self.switch.ports[h2.switch_link.intf1]
            logging.debug("Monitoring faucet event socket for target port add %d" % target_port)
            monitor.add_stream(self.faucet_events.sock)

            logging.debug("Monitoring dhcp responses from %s" % h1.name)
            filter="src port 67"
            dhcp_traffic = TcpHelper(h1, filter, vflags='', packets=1, duration_sec=60)
            monitor.add_stream(dhcp_traffic.stream())

            logging.debug("Activating target %s" % h2.name)
            h2.activate()

            for stream in monitor.generator():
                if stream == self.faucet_events.sock:
                    event = self.faucet_events.next_event()
                    if self.faucet_events.is_port_active_event(event) == target_port:
                        logging.debug('Switch port %d active' % target_port)
                        monitor.remove_stream(self.faucet_events.sock)
                elif stream == dhcp_traffic.stream():
                    dhcp_line = dhcp_traffic.next_line()
                    if dhcp_line:
                        match = re.search(self.DHCP_PATTERN, dhcp_line)
                        if match:
                            self.target_host = match.group(1)
                            logging.debug('Host %s is at %s' % (h2.name, self.target_host))
                            h2.setIP(self.target_host)
                            monitor.remove_stream(dhcp_traffic.stream())
                elif stream == None:
                    logging.debug('Waiting for monitors to clear...')
                else:
                    assert False, 'Unknown stream %s' % stream

            assert self.pingTest(h2, h1)
            assert self.pingTest(h1, h2)

            assert self.dockerTest('daq/test_ping')
            assert self.dockerTest('daq/test_nmap')
            assert self.dockerTest('daq/test_pass')
            assert not self.dockerTest('daq/test_fail')

            for num in range(1,100):
                assert self.dockerTest('daq/test_ping')

        except Exception as e:
            print e
        except KeyboardInterrupt:
            print 'Interrupted'

        CLI(self.net)

        logging.debug("Stopping faucet...")
        self.switch.cmd('docker kill daq-faucet')
        logging.debug("Stopping mininet...")
        self.net.stop()


if __name__ == '__main__':
    minilog.setLogLevel('info')
    if os.getuid() == 0:
        DAQRunner().runner()
    else:
        logger.debug("You are NOT root")
