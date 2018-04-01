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

    DHCP_MAC_PATTERN = '> ([0-9a-f:]+), ethertype IPv4'
    DHCP_IP_PATTERN = 'Your-IP ([0-9.]+)'

    DHCP_PATTERN = '(%s)|(%s)' % (DHCP_MAC_PATTERN, DHCP_IP_PATTERN)

    TEST_PREFIX = 'daq/test_'

    MONITOR_SCAN_SEC = 10

    TEST_IP_PREFIX = '192.168.84.'

    net = None
    switch = None
    target_ip = None
    run_id = None

    def addHost(self, name, cls=DAQHost, ip=None, env_vars=[], vol_maps=[]):
        params = { 'ip': ip } if ip else {}
        params['tmpdir'] = os.path.join(self.tmpdir, 'tests')
        params['env_vars'] = env_vars
        params['vol_maps'] = vol_maps
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

    def dockerTestName(self, image):
        # Names need to be short because they ultimately get used as netif names.
        assert image.startswith(self.TEST_PREFIX), 'name %s not startswith %s' % (image, self.TEST_PREFIX)
        return image[len(self.TEST_PREFIX):]

    def dockerTest(self, image):
        test_name = self.dockerTestName(image)
        env_vars = [ "TARGET_NAME=" + test_name,
                     "TARGET_IP=" + self.target_ip,
                     "TARGET_MAC=" + self.target_mac,
                     "GATEWAY_IP=" + self.networking.IP(),
                     "GATEWAY_MAC=" + self.networking.MAC()]
        vol_maps = [ self.scan_base + ":/scans" ]
        logging.debug("Running docker test %s" % image)
        cls = MakeFaucetDockerHost(image, prefix='daq')
        host = self.addHost(test_name, cls=cls, env_vars = env_vars, vol_maps=vol_maps)
        host.activate()
        error_code = host.wait()
        self.removeHost(host)
        if error_code != 0:
            logging.info("FAILED test %s with error %s" % (host.name, error_code))
        else:
            logging.info("PASSED test %s" % (host.name))
        return error_code == 0

    def get_device_intf(self):
        device_intf_name = os.getenv('DAQ_INTF')
        return Intf(device_intf_name, node=DummyNode())

    def set_run_id(self, run_id):
        self.run_id = run_id
        self.tmpdir = os.path.join('inst', 'run-' + run_id)
        self.scan_base = os.path.abspath(os.path.join(self.tmpdir, 'scans'))
        if not os.path.exists(self.scan_base):
            os.makedirs(self.scan_base)

    def make_test_run_id(self):
        return '%06x' % int(time.time())

    def runner(self):

        self.set_run_id('init')

        logging.debug("Creating miniet...")
        self.net = Mininet()

        logging.debug("Adding switches...")
        self.switch = self.net.addSwitch('pri', dpid='1', cls=OVSSwitch)

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

        logging.debug("Adding networking host...")
        self.networking = self.addHost('networking', cls=MakeFaucetDockerHost('daq/networking', prefix='daq'))
        networking = self.networking
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

        logging.info('Adding fake external device %s5' % self.TEST_IP_PREFIX)
        self.networking.cmd('ip addr add %s5 dev %s' % (self.TEST_IP_PREFIX, self.networking.switch_link.intf2))
        self.switch.cmd('ip route replace %s0/24 dev %s' % (self.TEST_IP_PREFIX, device_intf.name))

        try:
            assert self.pingTest(networking, dummy)
            assert self.pingTest(dummy, networking)

            while True:
                self.set_run_id(self.make_test_run_id())

                logging.info('')
                logging.info('Starting new test run %s' % self.run_id)

                logging.debug('Flushing event queue.')
                while self.faucet_events.has_event():
                    event = self.faucet_events.next_event()
                    logging.debug('Faucet event %s' % event)

                intf_name = device_intf.name
                if intf_name == 'faux' or intf_name == 'local':
                    logging.info('Flapping %s device interface.' % intf_name)
                    self.switch.cmd('ip link set %s down' % intf_name)
                    time.sleep(0.5)
                    self.switch.cmd('ip link set %s up' % intf_name)

                target_port = self.switch.ports[device_intf]
                logging.info('Waiting for port-up event on interface %s port %d...' %
                    (device_intf.name, target_port))
                while True:
                    event = self.faucet_events.next_event()
                    logging.debug('Faucet event %s' % event)
                    (port, active) = self.faucet_events.as_port_state(event)
                    if port == target_port and active:
                        break

                logging.info('Recieved port up event on port %d.' % target_port)
                logging.info('Waiting for dhcp reply from %s...' % networking.name)
                filter="src port 67"
                dhcp_traffic = TcpHelper(networking, filter, packets=None, duration_sec=None, logger=logger)

                while True:
                    dhcp_line = dhcp_traffic.next_line()
                    match = re.search(self.DHCP_PATTERN, dhcp_line)
                    if match:
                        self.target_ip = match.group(4)
                        if self.target_ip:
                            assert self.target_mac, 'Target MAC not scraped from dhcp response.'
                            break
                        else:
                            self.target_mac = match.group(2)
                dhcp_traffic.close()
                logging.info('Received reply, host %s is at %s/%s' % (intf_name, self.target_mac, self.target_ip))

                logging.info('Running background monitor scan for %d seconds...' % self.MONITOR_SCAN_SEC)
                monitor_file = os.path.join(self.scan_base, 'monitor.pcap')
                tcp_monitor = TcpHelper(self.switch, '', packets=None, duration_sec = self.MONITOR_SCAN_SEC,
                    pcap_out=monitor_file, intf_name=intf_name, logger=logger)
                assert tcp_monitor.wait() == 0, 'Failing executing monitor pcap'

                logging.info('Running test suite against target...')

                assert self.pingTest(networking, self.target_ip)

                self.dockerTest('daq/test_mudgee')

                assert self.dockerTest('daq/test_pass')
                assert not self.dockerTest('daq/test_fail')
                assert self.dockerTest('daq/test_ping')
                self.dockerTest('daq/test_bacnet')
                self.dockerTest('daq/test_nmap')

                logging.info('Done with tests')

        except Exception as e:
            print e, traceback.print_exc(file=sys.stderr)
        except KeyboardInterrupt:
            print 'Interrupted'

        logging.debug('Dropping into interactive command line')
        CLI(self.net)

        logging.debug('Cleaning up test route...')
        self.switch.cmd('ip route del %s0/24' % self.TEST_IP_PREFIX)
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
