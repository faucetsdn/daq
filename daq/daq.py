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

from ConfigParser import ConfigParser
from StringIO import StringIO

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
    IMAGE_NAME_FORMAT = 'daq/test_%s'
    CONTAINER_PREFIX = 'daq'

    DHCP_MAC_PATTERN = '> ([0-9a-f:]+), ethertype IPv4'
    DHCP_IP_PATTERN = 'Your-IP ([0-9.]+)'
    DHCP_PATTERN = '(%s)|(%s)' % (DHCP_MAC_PATTERN, DHCP_IP_PATTERN)

    ERROR_STATE = -1
    INIT_STATE = 0
    STARTUP_STATE = 1
    ACTIVE_STATE = 2
    DHCP_STATE = 3
    MONITOR_STATE = 4
    TEST_STATE = 5
    DONE_STATE = 6

    runner = None
    port_set = None
    pri_base = None
    run_id = None
    target_ip = None
    target_mac = None
    networking = None
    dummy = None
    state = None
    failures = None

    def __init__(self, runner, port_set):
        self.runner = runner
        self.port_set = port_set
        self.pri_base = port_set * 10
        self.run_id = '%06x' % int(time.time())
        self.tmpdir = os.path.join('inst', 'run-' + self.run_id)
        self.scan_base = os.path.abspath(os.path.join(self.tmpdir, 'scans'))
        self.state_transition(self.INIT_STATE)
        self.failures = []
        # There is a race condition here with ovs assigning ports, so wait a bit.
        logging.info('Set %d waiting to settle...' % port_set)
        time.sleep(2)
        self.state_transition(self.STARTUP_STATE, self.INIT_STATE)
        self.remaining_tests = self.make_tests()
        networking_name = 'gw%02d' % self.port_set
        networking_port = self.pri_base + self.NETWORKING_OFFSET
        logging.debug("Adding networking host on port %d" % networking_port)
        cls=MakeDockerHost('daq/networking', prefix=self.CONTAINER_PREFIX)
        self.networking = self.runner.addHost(networking_name, port=networking_port,
                cls=cls, tmpdir=self.tmpdir)

    def make_tests(self):
        return [ 'pass', 'fail', 'ping', 'bacnet', 'nmap', 'mudgee' ]

    def state_transition(self, to, expected=None):
        assert expected == None or self.state == expected, ('state was %d expected %d' %
                                                            (self.state, expected))
        logging.debug('Set %d state %s -> %d' % (self.port_set, self.state, to))
        self.state = to

    def cancel(self):
        self.networking.terminate()

    def activate(self):
        self.state_transition(self.ACTIVE_STATE, self.STARTUP_STATE)
        logging.info('Set %d activating.' % self.port_set)

        if not os.path.exists(self.scan_base):
            os.makedirs(self.scan_base)

        networking = self.networking
        networking.activate()

        dummy_name = 'dummy%02d' % self.port_set
        dummy_port = self.pri_base + self.DUMMY_OFFSET
        dummy = self.runner.addHost(dummy_name, port=dummy_port)
        self.dummy = dummy

        self.fake_target = self.TEST_IP_FORMAT % random.randint(10,99)
        logging.debug('Adding fake target at %s' % self.fake_target)
        networking.cmd('ip addr add %s dev %s' %
                (self.fake_target, networking.switch_link.intf2))

        # Dummy doesn't use DHCP, so need to set default route manually.
        dummy.cmd('route add -net 0.0.0.0 gw %s' % networking.IP())

        try:
            assert self.pingTest(networking, dummy), 'ping failed'
            assert self.pingTest(dummy, networking), 'ping failed'
            assert self.pingTest(dummy, self.fake_target), 'ping failed'
            assert self.pingTest(networking, dummy, src_addr=self.fake_target), 'ping failed'
        except Exception as e:
            logging.error('Set %d sanity error: %s' % (self.port_set, e))
            self.state_transition(self.ERROR_STATE, self.ACTIVE_STATE)
            self.failures.append('sanity')
            self.cleanup()

    def cleanup(self):
        logging.info('Set %d cleanup' % self.port_set)
        self.networking.terminate()
        self.runner.removeHost(self.networking)
        self.runner.removeHost(self.dummy)
        self.runner.target_set_complete(self)

    def idle_handler(self):
        if self.state == self.STARTUP_STATE:
            self.activate()
        elif self.state == self.ACTIVE_STATE:
            self.dhcp_wait()

    def pingTest(self, a, b, src_addr=None):
        b_name = b if isinstance(b, str) else b.name
        b_ip = b if isinstance(b, str) else b.IP()
        from_msg = ' from %s' % src_addr if src_addr else ''
        logging.info("Set %d ping test %s->%s%s" % (self.port_set, a.name, b_name, from_msg))
        failure="ping FAILED"
        assert b_ip != "0.0.0.0", "IP address not assigned, can't ping"
        src_opt = '-I %s' % src_addr if src_addr else ''
        output = a.cmd('ping -c2', src_opt, b_ip, '> /dev/null 2>&1 || echo ', failure).strip()
        return output.strip() != failure

    def dhcp_wait(self):
        self.state_transition(self.DHCP_STATE, self.ACTIVE_STATE)
        logging.info('Set %d waiting for dhcp reply from %s...' %
                     (self.port_set, self.networking.name))
        filter="src port 67"
        self.dhcp_traffic = TcpdumpHelper(self.networking, filter, packets=None,
                                          timeout=None, blocking=False)
        self.runner.monitor.monitor(self.dhcp_traffic.stream(), lambda: self.dhcp_line())

    def dhcp_line(self):
        dhcp_line = self.dhcp_traffic.next_line()
        if not dhcp_line:
            return
        match = re.search(self.DHCP_PATTERN, dhcp_line)
        if match:
            self.target_ip = match.group(4)
            if self.target_ip:
                assert self.target_mac, 'Target MAC not scraped from dhcp response.'
                self.dhcp_finalize()
            else:
                self.target_mac = match.group(2)

    def dhcp_finalize(self):
        self.runner.monitor.forget(self.dhcp_traffic.stream())
        self.dhcp_traffic.close()
        logging.info('Set %d received dhcp reply: %s is at %s' %
            (self.port_set, self.target_mac, self.target_ip))
        self.monitor_scan()

    def monitor_scan(self):
        self.state_transition(self.MONITOR_STATE, self.DHCP_STATE)
        logging.info('Set %d background scan for %d seconds...' %
                     (self.port_set, self.MONITOR_SCAN_SEC))
        intf_name = self.runner.sec_name
        monitor_file = os.path.join(self.scan_base, 'monitor.pcap')
        filter = 'vlan %d' % self.pri_base
        self.tcp_monitor = TcpdumpHelper(self.runner.pri, filter, packets=None, intf_name=intf_name,
                timeout=self.MONITOR_SCAN_SEC, pcap_out=monitor_file, blocking=False)
        self.runner.monitor.monitor(self.tcp_monitor.stream(), lambda: self.tcp_monitor.next_line(),
                hangup=lambda: self.monitor_complete())

    def monitor_complete(self):
        logging.info('Set %d monitor scan complete' % self.port_set)
        assert self.tcp_monitor.wait() == 0, 'Failed executing monitor pcap'
        self.state_transition(self.TEST_STATE, self.MONITOR_STATE)
        self.ping_tests()
        self.run_next_test()

    def ping_tests(self):
        assert self.pingTest(self.networking, self.target_ip)
        assert self.pingTest(self.networking, self.target_ip, src_addr=self.fake_target)

    def run_next_test(self):
        if len(self.remaining_tests):
            self.run_test(self.remaining_tests.pop(0))
        else:
            self.state_transition(self.DONE_STATE, self.TEST_STATE)
            self.cleanup()

    def run_test(self, test_name):
        logging.info('Set %d running test %s' % (self.port_set, test_name))
        host = self.docker_test(test_name)
        self.running_test = host

    def docker_test(self, test_name):
        self.test_name = test_name
        port = self.pri_base + self.TEST_OFFSET
        gateway = self.networking
        image = self.IMAGE_NAME_FORMAT % test_name
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
        pipe = host.activate(log_name = None)
        self.log_file = host.open_log()
        self.runner.monitor.monitor(pipe.stdout, copy_to=self.log_file,
                    hangup=lambda: self.docker_complete())
        return host

    def docker_complete(self):
        host = self.running_test
        self.running_test = None
        error_code = host.wait()
        self.runner.removeHost(host)
        self.log_file.close()
        if self.test_name == 'fail':
            error_code = 0 if error_code else 1
        if error_code != 0:
            logging.info("Set %d FAILED test %s with error %s" %
                         (self.port_set, self.test_name, error_code))
            self.failures.append(self.test_name)
        else:
            logging.info("Set %d PASSED test %s" % (self.port_set, self.test_name))
        self.run_next_test()


class DAQRunner():

    config = None
    net = None
    device_intfs = None
    target_sets = None
    result_sets = None
    pri = None
    sec = None
    sec_dpid = None
    sec_port = None
    sec_name = None

    def __init__(self, config):
        self.config = config
        self.target_sets = {}
        self.result_sets = {}

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
        intf_names = self.config['daq_intf'].split(',')
        intfs=[]
        for intf_name in intf_names:
            intf_name = intf_name[0:-1] if intf_name.endswith('!') else intf_name
            port_no = len(intfs) + 1
            intf = Intf(intf_name.strip(), node=DummyNode(), port=port_no)
            intf.port = port_no
            intfs.append(intf)
        return intfs

    def auto_start_sets(self):
        assert False, 'auto_start_sets not implemented'

    def flap_interface_ports(self):
        if self.device_intfs:
            for device_intf in self.device_intfs:
                self.flap_interface_port(device_intf.name)

    def flap_interface_port(self, intf_name):
        if intf_name.startswith('faux') or intf_name == 'local':
            logging.info('Flapping device interface %s.' % intf_name)
            self.sec.cmd('ip link set %s down' % intf_name)
            time.sleep(0.5)
            self.sec.cmd('ip link set %s up' % intf_name)

    def create_secondary(self):
        self.sec_port = int(self.config['ext_port'] if 'ext_port' in self.config else 47)
        if 'ext_dpid' in self.config:
            self.sec_dpid = int(self.config['ext_dpid'], 0)
            self.sec_name = self.config['ext_intf']
            logging.info('Configuring external secondary with dpid %s on intf %s' % (self.sec_dpid, self.sec_name))
            sec_intf = Intf(self.sec_name, node=DummyNode(), port=1)
            self.pri.addIntf(sec_intf, port=1)
        else:
            self.sec_dpid = 2
            logging.info('Creating ovs secondary with dpid/port %s/%d' % (self.sec_dpid, self.sec_port))
            self.sec = self.net.addSwitch('sec', dpid=str(self.sec_dpid), cls=OVSSwitch)

            link = self.net.addLink(self.pri, self.sec, port1=1,
                    port2=self.sec_port, fast=False)
            logging.info('Added switch link %s <-> %s' % (link.intf1.name, link.intf2.name))
            self.sec_name = link.intf2.name

    def initialize(self):
        logging.debug("Creating miniet...")
        self.net = Mininet()

        logging.debug("Adding switches...")
        self.pri = self.net.addSwitch('pri', dpid='1', cls=OVSSwitch)

        self.create_secondary()

        targetIp = "127.0.0.1"
        logging.debug("Adding controller at %s" % targetIp)
        controller = self.net.addController('controller', controller=RemoteController,
                ip=targetIp, port=6633 )

        logging.info("Starting mininet...")
        self.net.start()

        logging.info("Starting faucet...")
        output = self.pri.cmd('cmd/faucet && echo SUCCESS')
        if not output.strip().endswith('SUCCESS'):
            logging.info('Faucet output: %s' % output)
            assert False, 'Faucet startup failed'

        if self.sec:
            self.device_intfs = self.make_device_intfs()
            for device_intf in self.device_intfs:
                logging.info("Attaching device interface %s on port %d." %
                        (device_intf.name, device_intf.port))
                self.sec.addIntf(device_intf, port=device_intf.port)
                self.switchAttach(self.sec, device_intf)

        logging.debug("Attaching event channel...")
        self.faucet_events = FaucetEventClient()
        self.faucet_events.connect(os.getenv('FAUCET_EVENT_SOCK'))

        logging.info("Waiting for system to settle...")
        time.sleep(3)

        logging.debug('Done with initialization')

    def cleanup(self):
        logging.debug("Stopping faucet...")
        self.pri.cmd('docker kill daq-faucet')
        logging.debug("Stopping mininet...")
        self.net.stop()
        logging.info("Done with runner.")

    def handle_faucet_event(self):
        target_dpid = int(self.sec_dpid)
        event = self.faucet_events.next_event()
        logging.debug('Faucet event %s' % event)
        (dpid, port, active) = self.faucet_events.as_port_state(event)
        logging.debug('Port state is dpid %s port %s active %s' % (dpid, port, active))
        if dpid == target_dpid:
            if active:
                self.trigger_target_set(port)
            else:
                self.cancel_target_set(port)

    def handle_system_idle(self):
        for target_set in self.target_sets.values():
            target_set.idle_handler()

    def main_loop(self):
        self.one_shot = 's' in self.config['opts']
        self.flap_ports='f' in self.config['opts']
        self.auto_start='a' in self.config['opts']

        if self.auto_start:
            self.auto_start_sets()

        if self.flap_ports:
            self.flap_interface_ports()

        self.exception = False
        try:
            self.monitor = StreamMonitor(idle_handler=lambda: self.handle_system_idle())
            self.monitor.monitor(self.faucet_events.sock, lambda: self.handle_faucet_event())
            logging.info('Entering main event loop.')
            self.monitor.event_loop()
        except Exception as e:
            self.exception = e
            print e, traceback.print_exc(file=sys.stderr)
        except KeyboardInterrupt:
            print 'Interrupted'

        if not self.one_shot:
            logging.debug('Dropping into interactive command line')
            CLI(self.net)

    def trigger_target_set(self, port_set):
        if port_set >= self.sec_port:
            logging.debug('Ignoring phantom port set %d' % port_set)
            return
        assert not port_set in self.target_sets, 'target set %d already exists' % port_set
        logging.debug('Set %d connecting device' % port_set)
        target_set = ConnectedHost(self, port_set)
        self.target_sets[port_set] = target_set

    def target_set_complete(self, target_set):
        port_set = target_set.port_set
        failures = target_set.failures
        logging.info('Set %d complete, failures: %s' % (port_set, failures))
        del self.target_sets[port_set]
        self.result_sets[port_set] = failures
        logging.info('Remaining sets: %s' % self.target_sets.keys())
        if not self.target_sets and self.one_shot:
            self.monitor.forget(self.faucet_events.sock)

    def cancel_target_set(self, port_set):
        if port_set in self.target_sets:
            target_set = self.target_sets[port_set]
            del self.target_sets[port_set]
            target_set.cancel()
            logging.info('Set %d cancelled.' % port_set)

    def combine_failures(self):
        failures=[]
        for result_set in self.result_sets:
            for failure in self.result_sets[result_set]:
                failures.append('%s-%s' % (result_set, failure))
        return failures

    def finalize(self):
        failures = self.combine_failures()
        if failures:
            logging.info('Test failures: %s' % failures)
        if self.exception:
            logging.error('Exiting b/c of exception: %s' % self.exception)
        if failures or self.exception:
            sys.exit(1)

def configure_logging(config):
    daq_env = config['daq_loglevel'] if 'daq_loglevel' in config else None
    logging.basicConfig(level=LEVELS[daq_env] if daq_env else LEVELS['info'])

    mininet_env = config['mininet_loglevel'] if 'mininet_loglevel' in config else None
    LOGMSGFORMAT = '%(message)s'
    minilog.setLogLevel(mininet_env if mininet_env else 'info')

def read_config_into(filename, config):
    parser = ConfigParser()
    with open(filename) as stream:
        stream = StringIO("[top]\n" + stream.read())
        parser.readfp(stream)
    for item in parser.items('top'):
        config[item[0]] = item[1]

def parse_args(args):
    config = {}
    opts = {}
    config['opts'] = opts
    first = True
    for arg in args:
        if first:
            first = False
        elif arg[0] == '-':
            opts[arg[1:]] = True
        else:
            read_config_into(arg, config)
    return config


if __name__ == '__main__':
    assert os.getuid() == 0, 'Must run DAQ as root.'

    config = parse_args(sys.argv)

    configure_logging(config)

    runner = DAQRunner(config)
    runner.initialize()
    runner.main_loop()
    runner.cleanup()
    runner.finalize()
