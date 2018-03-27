#!/usr/bin/env python

"""Device Automated Qualification testing framework"""

import logging
import os
import re
import signal
import sys
import time
import traceback

from mininet import log as minilog
from mininet.log import LEVELS
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, Host, Link
from mininet.link import Intf
from mininet.cli import CLI

from tests.faucet_mininet_test_host import MakeFaucetDockerHost
from tests.faucet_mininet_test_topo import FaucetHostCleanup
from tests import faucet_mininet_test_util

from tcp_helper import TcpHelper
from faucet_event_client import FaucetEventClient

logger = logging.getLogger(__name__)

class DAQHost(FaucetHostCleanup, Host):
    """Base Mininet Host class, for Mininet-based tests."""

    pass

class DummyNode():
    def addIntf(self, node, port=None):
        pass
        #print 'add dummy intf %s to port %s' % (node.name, port)

    def cmd(self, cmd, *args, **kwargs):
        pass
        #print 'dummy cmd %s/%s/%s' % (cmd, args, kwargs)

class DAQRunner():

    DHCP_PATTERN = 'Your-IP ([0-9.]+)'

    net = None
    switch = None
    target_host = None

    def addHost(self, name, cls=DAQHost, ip=None, env_vars=[]):
        params = { 'ip': ip } if ip else {}
        params['tmpdir'] = 'inst'
        params['env_vars'] = env_vars
        host = self.net.addHost(name, cls, **params)
        host.switch_link = self.net.addLink(self.switch, host, fast=False)
        if self.net.built:
            host.configDefault()
            self.switchAttach(host.switch_link.intf1)
        return host

    def switchAttach(self, intf):
        self.switch.attach(intf)
        # This really should be done in attach, but currently only automatic on switch startup.
        self.switch.vsctl(self.switch.intfOpts(intf))

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
        b_name = b if isinstance(b, str) else b.name
        b_ip = b if isinstance(b, str) else b.IP()
        logging.info("Ping test %s->%s" % (a.name, b_name))
        failure="ping FAILED"
        assert b_ip != "0.0.0.0", "IP address not assigned, can't ping"
        output = a.cmd('ping -c2', b_ip, '> /dev/null 2>&1 || echo ', failure).strip()
        if output:
            print output
        return output.strip() != failure

    def dockerTest(self, image):
        container_name = image.split('/')[-1]
        env_vars = [ "TARGET_HOST=" + self.target_host ]
        logging.info("Running docker test %s" % image)
        cls = MakeFaucetDockerHost(image, prefix='daq')
        host = self.addHost(container_name, cls=cls, env_vars = env_vars)
        host.activate()
        error_code = host.wait()
        self.removeHost(host)
        if error_code != 0:
            logging.info("FAILED test %s with error %s" % (image, error_code))
        else:
            logging.info("PASSED test %s" % image)
        return error_code == 0

    def get_device_intf(self):
        device_intf_name = os.getenv('DAQ_INTF')
        return Intf(device_intf_name, node=DummyNode())

    def runner(self):
        logging.debug("Creating miniet...")
        self.net = Mininet()

        logging.debug("Adding switch...")
        self.switch = self.net.addSwitch('switch', dpid='1', cls=OVSSwitch)

        logging.info("Starting faucet...")
        output = self.switch.cmd('cmd/faucet && echo SUCCESS')
        if not output.strip().endswith('SUCCESS'):
            print output
            assert False, 'Faucet startup failed'

        logging.debug("Attaching event channel...")
        self.faucet_events = FaucetEventClient()
        self.faucet_events.connect(os.getenv('FAUCET_EVENT_SOCK'))

        targetIp = "127.0.0.1"
        logging.debug("Adding controller at %s" % targetIp)
        controller = self.net.addController( 'controller', controller=RemoteController, ip=targetIp, port=6633 )

        logging.debug("Adding hosts...")
        networking = self.addHost('networking', cls=MakeFaucetDockerHost('daq/networking', prefix='daq'))
        dummy = self.addHost('dummy')

        logging.info("Starting mininet...")
        self.net.start()

        logging.debug("Activating networking...")
        networking.activate()

        logging.info("Waiting for system to settle...")
        time.sleep(3)

        device_intf = self.get_device_intf()
        self.switch.addIntf(device_intf)
        logging.info("Attaching device interface %s..." % device_intf.name)
        self.switchAttach(device_intf)

        assert self.pingTest(networking, dummy)
        assert self.pingTest(dummy, networking)

        while True:
            try:
                logging.debug('Flushing event queue')
                while self.faucet_events.has_event():
                    self.faucet_events.next_event()

                target_port = self.switch.ports[device_intf]
                logging.info('Waiting for port-up event on port %d for %s...' %
                    (target_port, device_intf.name))
                while True:
                    (port, active) = self.faucet_events.as_port_state(
                        self.faucet_events.next_event())
                    if port == target_port and active:
                        break

                logging.info('Waiting for dhcp reply from %s...' % networking.name)
                filter="src port 67"
                dhcp_traffic = TcpHelper(networking, filter, packets=None, duration_sec=None)

                while True:
                    dhcp_line = dhcp_traffic.next_line()
                    match = re.search(self.DHCP_PATTERN, dhcp_line)
                    if match:
                        self.target_host = match.group(1)
                        logging.info('Host %s is at %s' % (device_intf.name, self.target_host))
                        break
                dhcp_traffic.close()

                logging.info('Running test suite against target...')

                assert self.pingTest(networking, self.target_host)

                assert self.dockerTest('daq/test_pass')
                assert not self.dockerTest('daq/test_fail')
                assert self.dockerTest('daq/test_ping')
                self.dockerTest('daq/test_nmap')

                logging.info('Done with tests')

            except Exception as e:
                print e, traceback.print_exc(file=sys.stderr)
            except KeyboardInterrupt:
                print 'Interrupted'
                break

        logging.debug("Stopping faucet...")
        self.switch.cmd('docker kill daq-faucet')
        logging.debug("Stopping mininet...")
        self.net.stop()
        logging.info("Done with runner.")


def configure_logging():

    daq_env = os.getenv('DAQ_LOGLEVEL')
    logging.basicConfig(level=LEVELS[daq_env] if daq_env else LEVELS['info'])

    mini_env = os.getenv('MININET_LOGLEVEL')
    LOGMSGFORMAT = '%(message)s'
    minilog.setLogLevel(mini_env if mini_env else 'info')


if __name__ == '__main__':
    configure_logging()
    if os.getuid() == 0:
        DAQRunner().runner()
    else:
        logger.debug("You are NOT root")
