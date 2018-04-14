#!/usr/bin/env python

"""Device Automated Qualification testing framework"""

import logging
import os
import random
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

from clib.docker_host import MakeDockerHost
from clib.mininet_test_topo import FaucetHostCleanup
import clib.mininet_test_util

from clib.tcpdump_helper import TcpdumpHelper
from faucet_event_client import FaucetEventClient

logger = logging.getLogger(__name__)

class DAQHost(FaucetHostCleanup, Host):
    """Base Mininet Host class, for Mininet-based tests."""
    pass


class DummyNode():
    def addIntf(self, node, port=None):
        pass

    def cmd(self, cmd, *args, **kwargs):
        pass

class DAQRunner():

    DHCP_MAC_PATTERN = '> ([0-9a-f:]+), ethertype IPv4'
    DHCP_IP_PATTERN = 'Your-IP ([0-9.]+)'

    DHCP_PATTERN = '(%s)|(%s)' % (DHCP_MAC_PATTERN, DHCP_IP_PATTERN)

    TEST_PREFIX = 'daq/test_'

    MONITOR_SCAN_SEC = 10

    TEST_IP_PREFIX = '192.168.84.'

    NETWORKING_OFFSET = 0
    DUMMY_OFFSET = 1
    TEST_OFFSET = 2

    net = None
    switch = None
    target_ip = None
    run_id = None

    def addHost(self, name, cls=DAQHost, ip=None, env_vars=[], vol_maps=[],
            port=None):
        params = { 'ip': ip } if ip else {}
        params['tmpdir'] = os.path.join(self.tmpdir, 'tests')
        params['env_vars'] = env_vars
        params['vol_maps'] = vol_maps
        host = self.net.addHost(name, cls, **params)
        host.switch_link = self.net.addLink(self.pri, host, port1=port, fast=False)
        if self.net.built:
            host.configDefault()
            self.switchAttach(self.pri, host.switch_link.intf1)
        return host

    def switchAttach(self, switch, intf):
        switch.attach(intf)
        # This really should be done in attach, but currently only automatic on switch startup.
        switch.vsctl(switch.intfOpts(intf))

    def switchDelIntf(self, switch, intf):
        del switch.intfs[switch.ports[intf]]
        del switch.ports[intf]
        del switch.nameToIntf[intf.name]

    def removeHost(self, host):
        intf = host.switch_link.intf1
        self.pri.detach(intf)
        self.switchDelIntf(self.pri, intf)
        intf.delete()
        del self.net.links[self.net.links.index(host.switch_link)]
        del self.net.hosts[self.net.hosts.index(host)]

    def stopHost(self, host):
        logging.debug("Stopping host " + host.name)
        host.terminate()

    def pingTest(self, a, b, src_addr=None):
        b_name = b if isinstance(b, str) else b.name
        b_ip = b if isinstance(b, str) else b.IP()
        from_msg = ' from %s' % src_addr if src_addr else ''
        logging.info("Ping test %s->%s%s" % (a.name, b_name, from_msg))
        failure="ping FAILED"
        assert b_ip != "0.0.0.0", "IP address not assigned, can't ping"
        src_opt = '-I %s' % src_addr if src_addr else ''
        output = a.cmd('ping -c2', src_opt, b_ip, '> /dev/null 2>&1 || echo ', failure).strip()
        if output:
            print output
        return output.strip() != failure

    def dockerTestName(self, image):
        # Names need to be short because they ultimately get used as netif names.
        error_msg = 'name %s not startswith %s' % (image, self.TEST_PREFIX)
        assert image.startswith(self.TEST_PREFIX), error_msg
        return image[len(self.TEST_PREFIX):]

    def dockerTest(self, image, port=None, gateway=None):
        test_name = self.dockerTestName(image)
        env_vars = [ "TARGET_NAME=" + test_name,
                     "TARGET_IP=" + self.target_ip,
                     "TARGET_MAC=" + self.target_mac,
                     "GATEWAY_IP=" + gateway.IP(),
                     "GATEWAY_MAC=" + gateway.MAC()]
        vol_maps = [ self.scan_base + ":/scans" ]
        logging.debug("Running docker test %s" % image)
        cls = MakeDockerHost(image, prefix='daq')
        host = self.addHost(test_name, port=port, cls=cls, env_vars = env_vars, vol_maps=vol_maps)
        host.activate()
        error_code = host.wait()
        self.removeHost(host)
        if error_code != 0:
            logging.info("FAILED test %s with error %s" % (host.name, error_code))
        else:
            logging.info("PASSED test %s" % (host.name))
        return error_code == 0

    def device_intfs(self):
        device_intf_name = os.getenv('DAQ_INTF')
        intf = Intf(device_intf_name, node=DummyNode(), port=1)
        intf.port = 1
        return [ intf ]

    def set_run_id(self, run_id):
        self.run_id = run_id
        self.tmpdir = os.path.join('inst', 'run-' + run_id)
        self.scan_base = os.path.abspath(os.path.join(self.tmpdir, 'scans'))
        if not os.path.exists(self.scan_base):
            os.makedirs(self.scan_base)

    def make_test_run_id(self):
        return '%06x' % int(time.time())

    def runner(self):
        one_shot = '-s' in sys.argv
        failed = False

        self.set_run_id('init')

        logging.debug("Creating miniet...")
        self.net = Mininet()

        logging.debug("Adding switches...")
        self.pri = self.net.addSwitch('pri', dpid='1', cls=OVSSwitch)
        self.sec = self.net.addSwitch('sec', dpid='2', cls=OVSSwitch)

        logging.info("Starting faucet...")
        output = self.pri.cmd('cmd/faucet && echo SUCCESS')
        if not output.strip().endswith('SUCCESS'):
            print output
            assert False, 'Faucet startup failed'

        logging.debug("Attaching event channel...")
        self.faucet_events = FaucetEventClient()
        self.faucet_events.connect(os.getenv('FAUCET_EVENT_SOCK'))

        targetIp = "127.0.0.1"
        logging.debug("Adding controller at %s" % targetIp)
        controller = self.net.addController('controller', controller=RemoteController,
                ip=targetIp, port=6633 )

        logging.info("Adding internal switch bridge")
        self.switch_link = self.net.addLink(self.pri, self.sec, port1=1, port2=47, fast=False)
        print self.switch_link.intf1.name, self.switch_link.intf2.name

        logging.info("Starting mininet...")
        self.net.start()

        logging.info("Waiting for system to settle...")
        time.sleep(3)

        device_intfs = self.device_intfs()
        for device_intf in device_intfs:
            logging.info("Attaching device interface %s..." % device_intf.name)
            self.sec.addIntf(device_intf, port=device_intf.port)
            self.switchAttach(self.sec, device_intf)

        try:
            while True:
                port_set = random.randint(1, 2)
                pri_base = port_set * 10
                self.set_run_id(self.make_test_run_id())
                logging.info('')
                logging.info('Testing port_set %d, run_id %s' % (port_set, self.run_id))

                logging.debug("Adding networking host...")
                networking = self.addHost('networking', port=pri_base + self.NETWORKING_OFFSET,
                        cls=MakeDockerHost('daq/networking', prefix='daq'))
                networking.activate()

                dummy = self.addHost('dummy', port=pri_base + self.DUMMY_OFFSET)

                fake_target = '%s5' % self.TEST_IP_PREFIX
                logging.info('Adding fake target at %s' % fake_target)
                networking.cmd('ip addr add %s5 dev %s' %
                                    (self.TEST_IP_PREFIX, networking.switch_link.intf2))
                # Dummy doesn't use DHCP, so need to set default route manually.
                dummy.cmd('route add -net 0.0.0.0 gw %s' % networking.IP())

                assert self.pingTest(networking, dummy)
                assert self.pingTest(dummy, networking)
                assert self.pingTest(dummy, fake_target)
                assert self.pingTest(networking, dummy, src_addr=fake_target)

                logging.info('Starting new test run %s' % self.run_id)

                logging.debug('Flushing event queue.')
                while self.faucet_events.has_event():
                    event = self.faucet_events.next_event()
                    logging.debug('Faucet event %s' % event)

                intf_name = device_intf.name
                if intf_name == 'faux' or intf_name == 'local':
                    logging.info('Flapping %s device interface.' % intf_name)
                    self.sec.cmd('ip link set %s down' % intf_name)
                    time.sleep(0.5)
                    self.sec.cmd('ip link set %s up' % intf_name)

                target_dpid = int(self.sec.dpid)
                logging.info('Waiting for port-up on dpid %d port %d...' % (target_dpid, port_set))
                while True:
                    event = self.faucet_events.next_event()
                    logging.debug('Faucet event %s' % event)
                    (dpid, port, active) = self.faucet_events.as_port_state(event)
                    if dpid == target_dpid and port == port_set and active:
                        break

                logging.info('Recieved port up event.')
                logging.info('Waiting for dhcp reply from %s...' % networking.name)
                filter="src port 67"
                dhcp_traffic = TcpdumpHelper(networking, filter, packets=None,
                                             timeout=None, logger=logger)

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
                logging.info('Received reply, host %s is at %s/%s' %
                             (intf_name, self.target_mac, self.target_ip))

                logging.info('Running background monitor scan for %d seconds...'
                             % self.MONITOR_SCAN_SEC)
                monitor_file = os.path.join(self.scan_base, 'monitor.pcap')
                tcp_monitor = TcpdumpHelper(self.pri, '', packets=None,
                    timeout=self.MONITOR_SCAN_SEC, pcap_out=monitor_file, intf_name=intf_name,
                    logger=logger)
                assert tcp_monitor.wait() == 0, 'Failing executing monitor pcap'

                logging.info('Running test suite against target...')

                test_port = pri_base + self.TEST_OFFSET
                assert self.pingTest(networking, self.target_ip)
                assert self.pingTest(networking, self.target_ip, src_addr=fake_target)
                assert self.dockerTest('daq/test_pass', port=test_port, gateway=networking)
                assert not self.dockerTest('daq/test_fail', port=test_port, gateway=networking)
                assert self.dockerTest('daq/test_ping', port=test_port, gateway=networking)
                self.dockerTest('daq/test_bacnet', port=test_port, gateway=networking)
                self.dockerTest('daq/test_nmap', port=test_port, gateway=networking)
                self.dockerTest('daq/test_mudgee', port=test_port, gateway=networking)

                logging.info('Done with tests')

                networking.terminate()
                self.removeHost(networking)
                self.removeHost(dummy)

                if one_shot:
                    break

        except Exception as e:
            failed = e
            print e, traceback.print_exc(file=sys.stderr)
        except KeyboardInterrupt:
            print 'Interrupted'

        if not one_shot:
            logging.debug('Dropping into interactive command line')
            CLI(self.net)

        logging.debug('Cleaning up test route...')
        self.pri.cmd('ip route del %s0/24' % self.TEST_IP_PREFIX)
        logging.debug("Stopping faucet...")
        self.pri.cmd('docker kill daq-faucet')
        logging.debug("Stopping mininet...")
        self.net.stop()
        logging.info("Done with runner.")

        if failed:
            print 'Exiting with error %s' % failed
            sys.exit(1)


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
