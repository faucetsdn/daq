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
from stream_monitor import StreamMonitor

logger = logging.getLogger(__name__)

class DAQHost(FaucetHostCleanup, Host):
    """Base Mininet Host class, for Mininet-based tests."""
    pass


class DummyNode():
    def addIntf(self, node, port=None):
        pass

    def cmd(self, cmd, *args, **kwargs):
        pass

class ConnectedHost():
    NETWORKING_OFFSET = 0
    DUMMY_OFFSET = 1
    TEST_OFFSET = 2

    TEST_IP_FORMAT = '192.168.84.%d'
    MONITOR_SCAN_SEC = 10
    IMAGE_PREFIX = 'daq/test_'
    CONTAINER_PREFIX = 'daq'

    DHCP_MAC_PATTERN = '> ([0-9a-f:]+), ethertype IPv4'
    DHCP_IP_PATTERN = 'Your-IP ([0-9.]+)'
    DHCP_PATTERN = '(%s)|(%s)' % (DHCP_MAC_PATTERN, DHCP_IP_PATTERN)

    runner = None
    port_set = None
    pri_base = None
    run_id = None
    target_ip = None
    target_mac = None
    networking = None
    dummy = None

    def __init__(self, runner, port_set):
        self.runner = runner
        self.port_set = port_set
        self.pri_base = port_set * 10
        self.run_id = '%06x' % int(time.time())
        self.tmpdir = os.path.join('inst', 'run-' + self.run_id)
        self.scan_base = os.path.abspath(os.path.join(self.tmpdir, 'scans'))
        if not os.path.exists(self.scan_base):
            os.makedirs(self.scan_base)

    def setup(self):
        pri_base = self.pri_base
        networking_name = 'gw%02d' % self.port_set
        networking_port = pri_base + self.NETWORKING_OFFSET
        logging.debug("Adding networking host on port %d" % networking_port)
        cls=MakeDockerHost('daq/networking', prefix=self.CONTAINER_PREFIX)
        networking = self.runner.addHost(networking_name, port=networking_port,
                    cls=cls, tmpdir=self.tmpdir)

        networking.activate()

        dummy_name = 'dummy%02d' % self.port_set
        dummy_port = pri_base + self.DUMMY_OFFSET
        dummy = self.runner.addHost(dummy_name, port=dummy_port)
        self.dummy = dummy

        self.fake_target = self.TEST_IP_FORMAT % random.randint(10,99)
        logging.info('Adding fake target at %s' % self.fake_target)
        networking.cmd('ip addr add %s dev %s' %
                (self.fake_target, networking.switch_link.intf2))

        # Dummy doesn't use DHCP, so need to set default route manually.
        dummy.cmd('route add -net 0.0.0.0 gw %s' % networking.IP())

        assert self.pingTest(networking, dummy)
        assert self.pingTest(dummy, networking)
        assert self.pingTest(dummy, self.fake_target)
        assert self.pingTest(networking, dummy, src_addr=self.fake_target)
        self.networking = networking

    def cleanup(self):
        self.networking.terminate()
        self.runner.removeHost(self.networking)
        self.runner.removeHost(self.dummy)

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

    def wait_for_dhcp(self):
        logging.info('Waiting for dhcp reply from %s...' % self.networking.name)
        filter="src port 67"
        dhcp_traffic = TcpdumpHelper(self.networking, filter, packets=None,timeout=None)

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
        logging.info('Received reply, %s is at %s' % (self.target_mac, self.target_ip))

    def monitor_scan(self, intf):
        logging.info('Running background monitor scan for %d seconds...' % self.MONITOR_SCAN_SEC)
        monitor_file = os.path.join(self.scan_base, 'monitor.pcap')
        filter = 'vlan %d' % self.pri_base
        tcp_monitor = TcpdumpHelper(self.runner.pri, filter, packets=None, intf_name=intf.name,
                timeout=self.MONITOR_SCAN_SEC, pcap_out=monitor_file)
        assert tcp_monitor.wait() == 0, 'Failed executing monitor pcap'

    def run_tests(self):
        assert self.pingTest(self.networking, self.target_ip)
        assert self.pingTest(self.networking, self.target_ip, src_addr=self.fake_target)
        assert self.dockerTest('daq/test_pass')
        assert not self.dockerTest('daq/test_fail')
        assert self.dockerTest('daq/test_ping')
        self.dockerTest('daq/test_bacnet')
        self.dockerTest('daq/test_nmap')
        self.dockerTest('daq/test_mudgee')
        logging.info('Done with tests')

    def dockerTestName(self, image):
        # Names need to be short because they ultimately get used as netif names.
        error_msg = 'name %s not startswith %s' % (image, self.IMAGE_PREFIX)
        assert image.startswith(self.IMAGE_PREFIX), error_msg
        return image[len(self.IMAGE_PREFIX):]

    def dockerTest(self, image):
        port = self.pri_base + self.TEST_OFFSET
        gateway = self.networking
        test_name = self.dockerTestName(image)
        host_name = '%s%02d' % (test_name, self.port_set)
        env_vars = [ "TARGET_NAME=" + host_name,
                     "TARGET_IP=" + self.target_ip,
                     "TARGET_MAC=" + self.target_mac,
                     "GATEWAY_IP=" + gateway.IP(),
                     "GATEWAY_MAC=" + gateway.MAC()]
        vol_maps = [ self.scan_base + ":/scans" ]

        logging.debug("Running docker test %s" % image)
        cls = MakeDockerHost(image, prefix=self.CONTAINER_PREFIX)
        host = self.runner.addHost(host_name, port=port, cls=cls, env_vars = env_vars,
            vol_maps=vol_maps, tmpdir=self.tmpdir)
        host.activate()
        error_code = host.wait()
        self.runner.removeHost(host)
        if error_code != 0:
            logging.info("FAILED test %s with error %s" % (test_name, error_code))
        else:
            logging.info("PASSED test %s" % (test_name))
        return error_code == 0


class DAQRunner():

    net = None
    device_intfs = None

    def addHost(self, name, cls=DAQHost, ip=None, env_vars=[], vol_maps=[],
                port=None, tmpdir=None):
        params = { 'ip': ip } if ip else {}
        params['tmpdir'] = os.path.join(tmpdir, 'tests') if tmpdir else None
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

    def make_device_intfs(self):
        intf_names = os.getenv('DAQ_INTF').split(',')
        intfs=[]
        for intf_name in intf_names:
            port_no = len(intfs) + 1
            intf = Intf(intf_name.strip(), node=DummyNode(), port=port_no)
            intf.port = port_no
            intfs.append(intf)
        return intfs

    def wait_for_port_up(self, port_set, intf_name=None):
        logging.debug('Flushing event queue.')
        while self.faucet_events.has_event():
            event = self.faucet_events.next_event()
            logging.debug('Faucet event %s' % event)

        if intf_name == 'faux' or intf_name == 'local':
            logging.info('Flapping device interface %s.' % intf_name)
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

    def initialize(self):
        logging.debug("Creating miniet...")
        self.net = Mininet()

        logging.debug("Adding switches...")
        self.pri = self.net.addSwitch('pri', dpid='1', cls=OVSSwitch)
        self.sec = self.net.addSwitch('sec', dpid='2', cls=OVSSwitch)

        self.switch_link = self.net.addLink(self.pri, self.sec, port1=1, port2=47, fast=False)
        logging.info('Added switch link %s <-> %s' %
                (self.switch_link.intf1.name, self.switch_link.intf2.name))

        targetIp = "127.0.0.1"
        logging.debug("Adding controller at %s" % targetIp)
        controller = self.net.addController('controller', controller=RemoteController,
                ip=targetIp, port=6633 )

        logging.info("Starting mininet...")
        self.net.start()

        logging.info("Starting faucet...")
        output = self.pri.cmd('cmd/faucet && echo SUCCESS')
        if not output.strip().endswith('SUCCESS'):
            print output
            assert False, 'Faucet startup failed'

        logging.debug("Attaching event channel...")
        self.faucet_events = FaucetEventClient()
        self.faucet_events.connect(os.getenv('FAUCET_EVENT_SOCK'))

        logging.info("Waiting for system to settle...")
        time.sleep(3)

        self.device_intfs = self.make_device_intfs()
        for device_intf in self.device_intfs:
            logging.info("Attaching device interface %s on port %d." %
                    (device_intf.name, device_intf.port))
            self.sec.addIntf(device_intf, port=device_intf.port)
            self.switchAttach(self.sec, device_intf)

        logging.debug('Done with initialization')

    def handle_faucet_event(self):
        print self.faucet_events.next_event()

    def main_loop(self):
        monitor = StreamMonitor()
        monitor.monitor(self.faucet_events.sock, lambda: self.handle_faucet_event())
        monitor.event_loop()

    def other_stuff(self):
        one_shot = '-s' in sys.argv
        failed = False
        try:
            while True:
                self.test_run()
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

        monitor.forget(self.faucet_events.sock)
        logging.debug("Stopping faucet...")
        self.pri.cmd('docker kill daq-faucet')
        logging.debug("Stopping mininet...")
        self.net.stop()
        logging.info("Done with runner.")

        if failed:
            print 'Exiting with error %s' % failed
            sys.exit(1)

    def test_run(self):
        target_set = ConnectedHost(self, random.randint(1, len(self.device_intfs)))
        device_intf = self.device_intfs[target_set.port_set - 1]
        intf_name = device_intf.name

        logging.info('')
        logging.info('Testing port_set %d, run_id %s' % (target_set.port_set, target_set.run_id))

        target_set.setup()

        logging.info('Test results in %s' % target_set.tmpdir)

        # Nobody seems to do this properly, so don't try for now.
        #self.wait_for_port_up(target_set.port_set, intf_name=intf_name)

        target_set.wait_for_dhcp()

        target_set.monitor_scan(self.switch_link.intf1)

        logging.info('Running test suite against target...')

        target_set.run_tests()

        target_set.cleanup()


def configure_logging():

    daq_env = os.getenv('DAQ_LOGLEVEL')
    logging.basicConfig(level=LEVELS[daq_env] if daq_env else LEVELS['info'])

    mini_env = os.getenv('MININET_LOGLEVEL')
    LOGMSGFORMAT = '%(message)s'
    minilog.setLogLevel(mini_env if mini_env else 'info')


if __name__ == '__main__':
    configure_logging()
    if os.getuid() == 0:
        runner = DAQRunner()
        runner.initialize()
        runner.main_loop()
    else:
        logger.debug('Must run DAQ as root.')
