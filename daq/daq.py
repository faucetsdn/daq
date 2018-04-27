#!/usr/bin/env python

"""Device Automated Qualification testing framework"""

import logging
import os
import random
import re
import shutil
import signal
import sys
import time
import traceback

from ConfigParser import ConfigParser
from StringIO import StringIO

from mininet import log as minilog
from mininet.log import LEVELS, MininetLogger
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

from gcp import GcpManager

logger = logging.getLogger('daq')
altlog = logging.getLogger('mininet')

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
    WAITING_STATE = 6
    DONE_STATE = 7

    runner = None
    port_set = None
    pri_base = None
    target_ip = None
    target_mac = None
    networking = None
    dummy = None
    state = None
    results = None
    running_test = None
    run_id = None

    def __init__(self, runner, port_set):
        self.runner = runner
        self.port_set = port_set
        self.pri_base = port_set * 10
        self.tmpdir = os.path.join('inst', 'run-port-%02d' % self.port_set)
        self.run_id = '%06x' % int(time.time())
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        self.scan_base = os.path.abspath(os.path.join(self.tmpdir, 'scans'))
        self.state_transition(self.INIT_STATE)
        self.results = []
        # There is a race condition here with ovs assigning ports, so wait a bit.
        logger.info('Set %d created.' % port_set)
        time.sleep(2)
        self.state_transition(self.STARTUP_STATE, self.INIT_STATE)
        self.remaining_tests = self.make_tests()
        networking_name = 'gw%02d' % self.port_set
        networking_port = self.pri_base + self.NETWORKING_OFFSET
        logger.debug("Adding networking host on port %d" % networking_port)
        cls=MakeDockerHost('daq/networking', prefix=self.CONTAINER_PREFIX)
        try:
            self.networking = self.runner.addHost(networking_name, port=networking_port,
                cls=cls, tmpdir=self.tmpdir)
        except:
            self.terminate(trigger=False)
            raise

    def make_tests(self):
        return [ 'pass', 'fail', 'ping', 'bacnet', 'nmap', 'mudgee' ]

    def state_transition(self, to, expected=None):
        assert expected == None or self.state == expected, ('state was %d expected %d' %
                                                            (self.state, expected))
        logger.debug('Set %d state %s -> %d' % (self.port_set, self.state, to))
        self.state = to

    def activate(self):
        self.state_transition(self.ACTIVE_STATE, self.STARTUP_STATE)
        logger.info('Set %d activating.' % self.port_set)
        self.record_result('startup')

        if not os.path.exists(self.scan_base):
            os.makedirs(self.scan_base)

        try:
            networking = self.networking
            networking.activate()

            dummy_name = 'dummy%02d' % self.port_set
            dummy_port = self.pri_base + self.DUMMY_OFFSET
            self.dummy = self.runner.addHost(dummy_name, port=dummy_port)
            dummy = self.dummy

            self.fake_target = self.TEST_IP_FORMAT % random.randint(10,99)
            logger.debug('Adding fake target at %s' % self.fake_target)
            networking.cmd('ip addr add %s dev %s' %
                (self.fake_target, networking.switch_link.intf2))

            # Dummy doesn't use DHCP, so need to set default route manually.
            dummy.cmd('route add -net 0.0.0.0 gw %s' % networking.IP())

            assert self.pingTest(networking, dummy), 'ping failed'
            assert self.pingTest(dummy, networking), 'ping failed'
            assert self.pingTest(dummy, self.fake_target), 'ping failed'
            assert self.pingTest(networking, dummy, src_addr=self.fake_target), 'ping failed'
        except Exception as e:
            logger.error('Set %d sanity error: %s' % (self.port_set, e))
            logger.exception(e)
            self.state_transition(self.ERROR_STATE, self.ACTIVE_STATE)
            self.record_result('sanity', exception=e)
            self.terminate()

    def terminate(self, trigger=True):
        logger.info('Set %d terminate' % self.port_set)
        if self.networking:
            try:
                self.networking.terminate()
                self.runner.removeHost(self.networking)
                self.networking = None
            except Exception as e:
                logger.error('Set %d terminating networking: %s' % (self.port_set, e))
                logger.exception(e)
        if self.dummy:
            try:
                self.dummy.terminate()
                self.runner.removeHost(self.dummy)
                self.dummy = None
            except Exception as e:
                logger.error('Set %d terminating dummy: %s' % (self.port_set, e))
                logger.exception(e)
        if self.running_test:
            try:
                self.running_test.terminate()
                self.runner.removeHost(self.running_test)
                self.running_test = None
            except Exception as e:
                logger.error('Set %d terminating test: %s' % (self.port_set, e))
                logger.exception(e)
        if trigger:
            self.runner.target_set_complete(self)

    def idle_handler(self):
        if self.state == self.STARTUP_STATE:
            self.activate()
        elif self.state == self.ACTIVE_STATE:
            self.dhcp_monitor()

    def pingTest(self, a, b, src_addr=None):
        b_name = b if isinstance(b, str) else b.name
        b_ip = b if isinstance(b, str) else b.IP()
        from_msg = ' from %s' % src_addr if src_addr else ''
        logger.info("Set %d ping test %s->%s%s" % (self.port_set, a.name, b_name, from_msg))
        failure="ping FAILED"
        assert b_ip != "0.0.0.0", "IP address not assigned, can't ping"
        src_opt = '-I %s' % src_addr if src_addr else ''
        output = a.cmd('ping -c2', src_opt, b_ip, '> /dev/null 2>&1 || echo ', failure).strip()
        return output.strip() != failure

    def dhcp_monitor(self):
        self.state_transition(self.DHCP_STATE, self.ACTIVE_STATE)
        logger.info('Set %d waiting for dhcp reply from %s...' %
                     (self.port_set, self.networking.name))
        filter="src port 67"
        self.dhcp_traffic = TcpdumpHelper(self.networking, filter, packets=None,
                                          timeout=None, blocking=False)
        self.runner.monitor.monitor(self.dhcp_traffic.stream(), lambda: self.dhcp_line(),
                    hangup=lambda: self.dhcp_hangup(), error=lambda e: self.monitor_error(e))

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

    def dhcp_cleanup(self):
        if self.dhcp_traffic:
            self.runner.monitor.forget(self.dhcp_traffic.stream())
            self.dhcp_traffic.close()
            self.dhcp_traffic = None

    def dhcp_finalize(self):
        self.dhcp_cleanup()
        logger.info('Set %d received dhcp reply: %s is at %s' %
            (self.port_set, self.target_mac, self.target_ip))
        self.record_result('dhcp', mac=self.target_mac, ip=self.target_ip)
        self.monitor_scan()

    def dhcp_hangup(self):
        logger.info('Set %d dhcp hangup' % self.port_set)
        self.dhcp_cleanup()
        self.state_transition(self.ACTIVE_STATE, self.DHCP_STATE)
        self.dhcp_monitor()

    def monitor_error(self, e):
        self.runner.target_set_error(self.port_set, e)

    def monitor_scan(self):
        self.state_transition(self.MONITOR_STATE, self.DHCP_STATE)
        logger.info('Set %d background scan for %d seconds...' %
                     (self.port_set, self.MONITOR_SCAN_SEC))
        intf_name = self.runner.sec_name
        monitor_file = os.path.join(self.scan_base, 'monitor.pcap')
        filter = 'vlan %d' % self.pri_base
        self.tcp_monitor = TcpdumpHelper(self.runner.pri, filter, packets=None, intf_name=intf_name,
                timeout=self.MONITOR_SCAN_SEC, pcap_out=monitor_file, blocking=False)
        self.runner.monitor.monitor(self.tcp_monitor.stream(), lambda: self.tcp_monitor.next_line(),
                hangup=lambda: self.monitor_complete(), error=lambda e: self.monitor_error(e))

    def monitor_complete(self):
        logger.info('Set %d monitor scan complete' % self.port_set)
        assert self.tcp_monitor.wait() == 0, 'Failed executing monitor pcap'
        self.state_transition(self.TEST_STATE, self.MONITOR_STATE)
        self.ping_tests()
        self.run_next_test()

    def ping_tests(self):
        assert self.pingTest(self.networking, self.target_ip), 'simple ping failed'
        assert self.pingTest(self.networking, self.target_ip, src_addr=self.fake_target), 'target ping failed'

    def run_next_test(self):
        if len(self.remaining_tests):
            self.run_test(self.remaining_tests.pop(0))
        else:
            self.state_transition(self.DONE_STATE, self.TEST_STATE)
            self.record_result('finish')
            self.terminate()

    def run_test(self, test_name):
        logger.info('Set %d running test %s' % (self.port_set, test_name))
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

        logger.debug("Set %d running docker test %s" % (self.port_set, image))
        cls = MakeDockerHost(image, prefix=self.CONTAINER_PREFIX)
        host = self.runner.addHost(host_name, port=port, cls=cls, env_vars = env_vars,
            vol_maps=vol_maps, tmpdir=self.tmpdir)
        try:
            pipe = host.activate(log_name = None)
            self.log_file = host.open_log()
            self.state_transition(self.WAITING_STATE, self.TEST_STATE)
            self.runner.monitor.monitor(pipe.stdout, copy_to=self.log_file,
                hangup=lambda: self.docker_complete(), error=lambda e: self.monitor_error(e))
        except:
            host.terminate()
            raise
        return host

    def docker_complete(self):
        self.state_transition(self.TEST_STATE, self.WAITING_STATE)
        host = self.running_test
        self.running_test = None
        try:
            error_code = host.wait()
            self.runner.removeHost(host)
            self.log_file.close()
        except Exception as e:
            error_code = e
        logger.debug("Set %d docker complete, return=%s" % (self.port_set, error_code))
        if self.test_name == 'fail':
            error_code = 0 if error_code else 1
        self.record_result(self.test_name, code=error_code)
        if error_code:
            logger.info("Set %d FAILED test %s with error %s" %
                         (self.port_set, self.test_name, error_code))
        else:
            logger.info("Set %d PASSED test %s" % (self.port_set, self.test_name))
        self.run_next_test()

    def record_result(self, name, **kwargs):
        result = {
            'name': name,
            'runid': self.run_id,
            'timetstamp': int(time.time()),
            'port': self.port_set
        }
        for arg in kwargs:
            result[arg] = str(kwargs[arg])
        self.results.append(result)
        self.runner.gcp.publish_message('daq_runner', result)


class DAQRunner():

    config = None
    net = None
    device_intfs = None
    target_sets = None
    active_ports = None
    result_sets = None
    pri = None
    sec = None
    sec_dpid = None
    sec_port = None
    sec_name = None
    gcp = None

    def __init__(self, config):
        self.config = config
        self.target_sets = {}
        self.result_sets = {}
        self.active_ports = {}
        self.gcp = GcpManager(self.config)

    def addHost(self, name, cls=DAQHost, ip=None, env_vars=[], vol_maps=[],
                port=None, tmpdir=None):
        params = { 'ip': ip } if ip else {}
        params['tmpdir'] = os.path.join(tmpdir, 'tests') if tmpdir else None
        params['env_vars'] = env_vars
        params['vol_maps'] = vol_maps
        host = self.net.addHost(name, cls, **params)
        try:
            logger.debug('Created host %s with pid %s/%s' % (name, host.pid, host.shell.pid))
            host.switch_link = self.net.addLink(self.pri, host, port1=port, fast=False)
            if self.net.built:
                host.configDefault()
                self.switchAttach(self.pri, host.switch_link.intf1)
        except:
            host.terminate()
            raise
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
        logger.debug("Stopping host " + host.name)
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

    def flush_faucet_events(self):
        logger.info('Flushing faucet event queue...')
        while self.faucet_events.next_event():
            pass

    def flap_interface_ports(self):
        if self.device_intfs:
            for device_intf in self.device_intfs:
                self.flap_interface_port(device_intf.name)

    def flap_interface_port(self, intf_name):
        if intf_name.startswith('faux') or intf_name == 'local':
            logger.info('Flapping device interface %s.' % intf_name)
            self.sec.cmd('ip link set %s down' % intf_name)
            time.sleep(0.5)
            self.sec.cmd('ip link set %s up' % intf_name)

    def create_secondary(self):
        self.sec_port = int(self.config['ext_port'] if 'ext_port' in self.config else 47)
        if 'ext_dpid' in self.config:
            self.sec_dpid = int(self.config['ext_dpid'], 0)
            self.sec_name = self.config['ext_intf']
            logger.info('Configuring external secondary with dpid %s on intf %s' % (self.sec_dpid, self.sec_name))
            sec_intf = Intf(self.sec_name, node=DummyNode(), port=1)
            self.pri.addIntf(sec_intf, port=1)
        else:
            self.sec_dpid = 2
            logger.info('Creating ovs secondary with dpid/port %s/%d' % (self.sec_dpid, self.sec_port))
            self.sec = self.net.addSwitch('sec', dpid=str(self.sec_dpid), cls=OVSSwitch)

            link = self.net.addLink(self.pri, self.sec, port1=1,
                    port2=self.sec_port, fast=False)
            logger.info('Added switch link %s <-> %s' % (link.intf1.name, link.intf2.name))
            self.sec_name = link.intf2.name

    def initialize(self):
        self.gcp.publish_message('daq_runner', { 'name': 'init' })

        logger.debug("Creating miniet...")
        self.net = Mininet()

        logger.debug("Adding switches...")
        self.pri = self.net.addSwitch('pri', dpid='1', cls=OVSSwitch)

        logger.info("Starting faucet...")
        output = self.pri.cmd('cmd/faucet && echo SUCCESS')
        if not output.strip().endswith('SUCCESS'):
            logger.info('Faucet output: %s' % output)
            assert False, 'Faucet startup failed'

        self.create_secondary()

        targetIp = "127.0.0.1"
        logger.debug("Adding controller at %s" % targetIp)
        controller = self.net.addController('controller', controller=RemoteController,
                ip=targetIp, port=6633 )

        logger.info("Starting mininet...")
        self.net.start()

        if self.sec:
            self.device_intfs = self.make_device_intfs()
            for device_intf in self.device_intfs:
                logger.info("Attaching device interface %s on port %d." %
                        (device_intf.name, device_intf.port))
                self.sec.addIntf(device_intf, port=device_intf.port)
                self.switchAttach(self.sec, device_intf)

        logger.debug("Attaching event channel...")
        self.faucet_events = FaucetEventClient()
        self.faucet_events.connect(os.getenv('FAUCET_EVENT_SOCK'))

        logger.info("Waiting for system to settle...")
        time.sleep(3)

        logger.debug('Done with initialization')

    def cleanup(self):
        try:
            logger.debug("Stopping faucet...")
            self.pri.cmd('docker kill daq-faucet')
        except Exception as e:
            logger.error('Exception: %s' % e)
        try:
            logger.debug("Stopping mininet...")
            self.net.stop()
        except Exception as e:
            logger.error('Exception: %s' % e)
        logger.info("Done with runner.")

    def handle_faucet_event(self):
        target_dpid = int(self.sec_dpid)
        while True:
            event = self.faucet_events.next_event()
            logger.debug('Faucet event %s' % event)
            if not event:
                break
            (dpid, port, active) = self.faucet_events.as_port_state(event)
            logger.debug('Port state is dpid %s port %s active %s' % (dpid, port, active))
            if dpid == target_dpid:
                if active:
                    self.active_ports[port] = True
                    self.trigger_target_set(port)
                else:
                    self.active_ports[port] = False
                    self.cancel_target_set(port)

    def handle_system_idle(self):
        for target_set in self.target_sets.values():
            target_set.idle_handler()
        if self.auto_start and not self.one_shot:
            for port_set in self.active_ports.keys():
                if self.active_ports[port_set] and not port_set in self.target_sets:
                    self.trigger_target_set(port_set)
        if not self.target_sets and self.one_shot:
            self.monitor.forget(self.faucet_events.sock)

    def loop_hook(self):
        states = {}
        for key in self.target_sets.keys():
            states[key] = self.target_sets[key].state
        logger.debug('Active target sets/state: %s' % states)

    def main_loop(self):
        self.one_shot = self.config.get('s')
        self.flap_ports = self.config.get('f')
        self.auto_start = self.config.get('a')

        if self.flap_ports:
            self.flap_interface_ports()

        self.exception = False
        try:
            self.monitor = StreamMonitor(idle_handler=lambda: self.handle_system_idle(),
                                         loop_hook=lambda: self.loop_hook())
            self.monitor.monitor(self.faucet_events.sock, lambda: self.handle_faucet_event())
            if not self.auto_start:
                self.flush_faucet_events()
            logger.info('Entering main event loop.')
            self.monitor.event_loop()
        except Exception as e:
            logger.info('Event loop exception: %s' % e)
            logger.exception(e)
            self.exception = e
        except KeyboardInterrupt:
            logger.info('Keyboard Interrupt')

        if not self.one_shot:
            logger.info('Dropping into interactive command line')
            CLI(self.net)

    def trigger_target_set(self, port_set):
        if port_set >= self.sec_port:
            logger.debug('Ignoring phantom port set %d' % port_set)
            return
        assert not port_set in self.target_sets, 'target set %d already exists' % port_set
        try:
            logger.debug('Trigger target set %d' % port_set)
            self.target_sets[port_set] = ConnectedHost(self, port_set)
        except Exception as e:
            self.target_set_error(port_set, e)

    def target_set_error(self, port_set, e):
        logger.info('Set %d exception: %s' % (port_set, e))
        logger.exception(e)
        if port_set in self.target_sets:
            target_set = self.target_sets[port_set]
            target_set.record_result('exception', exception=e)
            target_set.terminate()
            self.target_set_complete(target_set)
        else:
            self.target_set_finalize(port_set, [str(e)])

    def target_set_complete(self, target_set):
        port_set = target_set.port_set
        results = target_set.results
        if port_set in self.target_sets:
            del self.target_sets[port_set]
        self.target_set_finalize(port_set, results)

    def target_set_finalize(self, port_set, results):
        logger.info('Set %d complete, %d results' % (port_set, len(results)))
        self.result_sets[port_set] = results
        logger.info('Remaining sets: %s' % self.target_sets.keys())

    def cancel_target_set(self, port_set):
        if port_set in self.target_sets:
            target_set = self.target_sets[port_set]
            del self.target_sets[port_set]
            target_set.terminate()
            logger.info('Set %d cancelled.' % port_set)

    def combine_results(self):
        results=[]
        for result_set in self.result_sets:
            for result in self.result_sets[result_set]:
                code = int(result['code']) if 'code' in result else 0
                if code != 0:
                    results.append('%02d:%s:%s' % (result_set, result['name'], code))
        return results

    def finalize(self):
        failures = self.combine_results()
        if failures:
            logger.error('Test failures: %s' % failures)
        if self.exception:
            logger.error('Exiting b/c of exception: %s' % self.exception)
        if failures or self.exception:
            sys.exit(1)

def mininet_alt_logger(self, level, msg, *args, **kwargs ):
    stripped = msg.strip()
    if stripped:
        altlog._log(level, stripped, *args, **kwargs)

def configure_logging(config):
    daq_env = config.get('daq_loglevel')
    logging.basicConfig(level=LEVELS.get(daq_env, LEVELS['info']))

    mininet_env = config.get('mininet_loglevel')
    minilog.setLogLevel(mininet_env if mininet_env else 'info')

    MininetLogger._log = mininet_alt_logger

def read_config_into(filename, config):
    parser = ConfigParser()
    with open(filename) as stream:
        stream = StringIO("[top]\n" + stream.read())
        parser.readfp(stream)
    for item in parser.items('top'):
        config[item[0]] = item[1]

def parse_args(args):
    config = {}
    first = True
    for arg in args:
        if first:
            first = False
        elif arg[0] == '-':
            config[arg[1:]] = True
        elif '=' in arg:
            parts = arg.split('=', 1)
            config[parts[0]] = parts[1]
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
