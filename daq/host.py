"""Represent a device-under-test"""

import logging
import math
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

logger = logging.getLogger('host')

class ConnectedHost():
    """Class managing a device-under-test"""

    NETWORKING_OFFSET = 0
    DUMMY_OFFSET = 1
    TEST_OFFSET = 2

    TEST_IP_FORMAT = '192.168.84.%d'
    MONITOR_SCAN_SEC = 20
    IMAGE_NAME_FORMAT = 'daq/test_%s'
    CONTAINER_PREFIX = 'daq'

    DHCP_MAC_PATTERN = '> ([0-9a-f:]+), ethertype IPv4'
    DHCP_IP_PATTERN = 'Your-IP ([0-9.]+)'
    DHCP_PATTERN = '(%s)|(%s)' % (DHCP_MAC_PATTERN, DHCP_IP_PATTERN)
    DHCP_TIMEOUT_SEC = 240
    DHCP_THRESHHOLD_SEC = 20

    ERROR_STATE = -1
    INIT_STATE = 0
    STARTUP_STATE = 1
    ACTIVE_STATE = 2
    DHCP_STATE = 3
    BASE_STATE = 4
    MONITOR_STATE = 6
    READY_STATE = 7
    TESTING_STATE = 8
    DONE_STATE = 9

    TEST_LIST = [ 'pass', 'fail', 'ping', 'bacnet', 'nmap', 'mudgee' ]
    TEST_ORDER = [ 'startup', 'sanity', 'dhcp', 'base',
            'monitor' ] + TEST_LIST + [ 'finish', 'info', 'timer' ]

    runner = None
    port_set = None
    pri_base = None
    target_ip = None
    target_mac = None
    networking = None
    dummy = None
    state = ERROR_STATE
    results = None
    running_test = None
    remaining_tests = None
    run_id = None
    test_name = 'unknown'
    test_start = None
    tcp_monitor = None
    dhcp_traffic = None

    def __init__(self, runner, port_set):
        self.runner = runner
        self.port_set = port_set
        self.pri_base = port_set * 10
        self.tmpdir = os.path.join('inst', 'run-port-%02d' % self.port_set)
        self.run_id = '%06x' % int(time.time())
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        self.scan_base = os.path.abspath(os.path.join(self.tmpdir, 'scans'))
        self.state_transition(self.INIT_STATE)
        self.results = {}
        self.record_result('startup', state='run')
        self.dhcp_try = 1
        logger.info('Set %d created.' % port_set)
        # There is a race condition here with ovs assigning ports, so wait a bit.
        time.sleep(2)
        self.remaining_tests = list(self.TEST_LIST)
        networking_name = 'gw%02d' % self.port_set
        networking_port = self.pri_base + self.NETWORKING_OFFSET
        logger.debug("Adding networking host on port %d" % networking_port)
        cls=MakeDockerHost('daq/networking', prefix=self.CONTAINER_PREFIX)
        try:
            self.networking = self.runner.add_host(networking_name, port=networking_port,
                cls=cls, tmpdir=self.tmpdir)
            self.record_result('startup')
        except:
            self.terminate(trigger=False)
            raise

    def state_transition(self, to, expected=None):
        assert expected == None or self.state == expected, ('state was %d expected %d' %
                                                            (self.state, expected))
        logger.debug('Set %d state %s -> %d' % (self.port_set, self.state, to))
        self.state = to

    def activate(self):
        self.state_transition(self.STARTUP_STATE, self.INIT_STATE)
        logger.info('Set %d activating.' % self.port_set)

        if not os.path.exists(self.scan_base):
            os.makedirs(self.scan_base)

        try:
            self.record_result('sanity', state='run')
            networking = self.networking
            networking.activate()
            self.startup_scan()

            dummy_name = 'dummy%02d' % self.port_set
            dummy_port = self.pri_base + self.DUMMY_OFFSET
            self.dummy = self.runner.add_host(dummy_name, port=dummy_port)
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
            self.record_result('sanity');
            self.state_transition(self.ACTIVE_STATE, self.STARTUP_STATE)
        except Exception as e:
            logger.error('Set %d sanity error: %s' % (self.port_set, e))
            logger.exception(e)
            self.record_result('sanity', exception=e);
            self.terminate()

    def terminate(self, trigger=True):
        logger.info('Set %d terminate, trigger %s' % (self.port_set, trigger))
        self.state_transition(self.ERROR_STATE)
        self.dhcp_cleanup()
        self.monitor_cleanup()
        if self.networking:
            try:
                self.networking.terminate()
                self.runner.remove_host(self.networking)
                self.networking = None
            except Exception as e:
                logger.error('Set %d terminating networking: %s' % (self.port_set, e))
                logger.exception(e)
        if self.dummy:
            try:
                self.dummy.terminate()
                self.runner.remove_host(self.dummy)
                self.dummy = None
            except Exception as e:
                logger.error('Set %d terminating dummy: %s' % (self.port_set, e))
                logger.exception(e)
        if self.running_test:
            try:
                self.running_test.terminate()
                self.runner.remove_host(self.running_test)
                self.running_test = None
            except Exception as e:
                logger.error('Set %d terminating test: %s' % (self.port_set, e))
                logger.exception(e)
        if trigger:
            self.runner.target_set_complete(self)

    def idle_handler(self):
        if self.state == self.INIT_STATE:
            self.activate()
        elif self.state == self.ACTIVE_STATE:
            self.dhcp_monitor()
        elif self.state == self.BASE_STATE:
            self.base_start()

    def pingTest(self, a, b, src_addr=None):
        b_name = b if isinstance(b, str) else b.name
        b_ip = b if isinstance(b, str) else b.IP()
        from_msg = ' from %s' % src_addr if src_addr else ''
        logger.info("Set %d ping test %s->%s%s" % (self.port_set, a.name, b_name, from_msg))
        failure="ping FAILED"
        assert b_ip != "0.0.0.0", "IP address not assigned, can't ping"
        src_opt = '-I %s' % src_addr if src_addr else ''
        try:
            output = a.cmd('ping -c2', src_opt, b_ip, '> /dev/null 2>&1 || echo ', failure).strip()
            return output.strip() != failure
        except Exception as e:
            logger.info('Set %d ping failure: %s' % (self.port_set, e))
            return False

    def startup_scan(self):
        assert not self.tcp_monitor, 'tcp_monitor already active'
        logger.debug('Set %d startup pcap start' % self.port_set)
        filter = ''
        self.startup_file = os.path.join('/tmp','startup.pcap')
        self.tcp_monitor = TcpdumpHelper(self.networking, filter, packets=None,
                timeout=None, pcap_out=self.startup_file, blocking=False)
        self.runner.monitor.monitor('tcpdump', self.tcp_monitor.stream(), lambda: self.tcp_monitor.next_line(),
                hangup=lambda: self.monitor_error(Exception('startup scan hangup')), error=lambda e: self.monitor_error(e))

    def dhcp_monitor(self):
        self.state_transition(self.DHCP_STATE, self.ACTIVE_STATE)
        self.record_result('dhcp', state='run')
        logger.info('Set %d waiting for dhcp reply from %s...' % (self.port_set, self.networking.name))
        filter="src port 67"
        self.dhcp_traffic = TcpdumpHelper(self.networking, filter, packets=None,
                    timeout=self.DHCP_TIMEOUT_SEC, blocking=False)
        self.runner.monitor.monitor(self.networking.name, self.dhcp_traffic.stream(), lambda: self.dhcp_line(),
                    hangup=lambda: self.dhcp_hangup(), error=lambda e: self.dhcp_error(e))

    def dhcp_line(self):
        dhcp_line = self.dhcp_traffic.next_line()
        if not dhcp_line:
            return
        match = re.search(self.DHCP_PATTERN, dhcp_line)
        if match:
            self.target_ip = match.group(4)
            if self.target_ip:
                assert self.target_mac, 'dhcp IP %s found, but no MAC address: %s' % (self.target_ip, dhcp_line)
                self.dhcp_success()
            else:
                self.target_mac = match.group(2)

    def dhcp_cleanup(self, forget=True):
        if self.dhcp_traffic:
            if forget:
                self.runner.monitor.forget(self.dhcp_traffic.stream())
            self.dhcp_traffic.terminate()
            self.dhcp_traffic = None

    def dhcp_success(self):
        self.dhcp_cleanup()
        delta = int(time.time()) - self.test_start
        logger.info('Set %d received dhcp reply after %ds: %s is at %s' %
            (self.port_set, delta, self.target_mac, self.target_ip))
        weak_result = delta > self.DHCP_THRESHHOLD_SEC
        state = 'weak' if weak_result else None
        self.record_result('dhcp', info=self.target_mac, ip=self.target_ip, state=state)
        self.state_transition(self.BASE_STATE, self.DHCP_STATE)

    def dhcp_hangup(self):
        try:
            raise Exception('dhcp hangup')
        except Exception as e:
            self.dhcp_error(e)

    def dhcp_error(self, e):
        logger.error('Set %d dhcp error: %s' % (self.port_set, e))
        self.record_result('dhcp', exception=e)
        self.dhcp_cleanup(forget=False)
        self.state_transition(self.ERROR_STATE, self.DHCP_STATE)
        self.runner.target_set_error(self.port_set, e)
        self.terminate()

    def base_start(self):
        try:
            self.base_tests()
            self.monitor_cleanup()
            logger.info('Set %d done with base.' % self.port_set)
            self.monitor_scan()
        except Exception as e:
            self.monitor_cleanup()
            self.monitor_error(e)

    def monitor_cleanup(self, forget=True):
        if self.tcp_monitor:
            logger.debug('Set %d monitor scan cleanup (forget=%s)' % (self.port_set, forget))
            if forget:
                self.runner.monitor.forget(self.tcp_monitor.stream())
            self.tcp_monitor.terminate()
            self.tcp_monitor = None

    def monitor_error(self, e):
        logger.error('Set %d monitor error: %s' % (self.port_set, e))
        self.monitor_cleanup(forget=False)
        self.record_result(self.test_name, exception=e)
        self.runner.target_set_error(self.port_set, e)

    def monitor_scan(self):
        self.state_transition(self.MONITOR_STATE, self.BASE_STATE)
        self.record_result('monitor', time=self.MONITOR_SCAN_SEC, state='run')
        logger.info('Set %d background scan for %d seconds...' %
                     (self.port_set, self.MONITOR_SCAN_SEC))
        intf_name = self.runner.sec_name
        monitor_file = os.path.join(self.scan_base, 'monitor.pcap')
        filter = 'vlan %d' % self.pri_base
        assert not self.tcp_monitor, 'tcp_monitor already active'
        self.tcp_monitor = TcpdumpHelper(self.runner.pri, filter, packets=None, intf_name=intf_name,
                timeout=self.MONITOR_SCAN_SEC, pcap_out=monitor_file, blocking=False)
        self.runner.monitor.monitor('tcpdump', self.tcp_monitor.stream(), lambda: self.tcp_monitor.next_line(),
                hangup=lambda: self.monitor_complete(), error=lambda e: self.monitor_error(e))

    def monitor_complete(self):
        logger.info('Set %d monitor scan complete' % self.port_set)
        self.monitor_cleanup(forget=False)
        self.record_result('monitor')
        self.state_transition(self.READY_STATE, self.MONITOR_STATE)
        self.run_next_test()

    def base_tests(self):
        self.record_result('base', state='run')
        if not self.pingTest(self.networking, self.target_ip):
            logger.debug('Set %d warmup ping failed' % self.port_set)
        try:
            assert self.pingTest(self.networking, self.target_ip), 'simple ping failed'
            assert self.pingTest(self.networking, self.target_ip, src_addr=self.fake_target), 'target ping failed'
        except:
            self.monitor_cleanup()
            raise
        self.record_result('base')

    def run_next_test(self):
        if len(self.remaining_tests):
            self.docker_test(self.remaining_tests.pop(0))
        else:
            self.state_transition(self.DONE_STATE, self.READY_STATE)
            self.record_result('finish')
            self.terminate()

    def docker_test(self, test_name):
        logger.info('Set %d running docker test %s' % (self.port_set, test_name))
        self.record_result(test_name, state='run')
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
        host = self.runner.add_host(host_name, port=port, cls=cls, env_vars = env_vars,
            vol_maps=vol_maps, tmpdir=self.tmpdir)
        try:
            pipe = host.activate(log_name = None)
            self.docker_log = host.open_log()
            self.state_transition(self.TESTING_STATE, self.READY_STATE)
            self.runner.monitor.monitor(host_name, pipe.stdout, copy_to=self.docker_log,
                hangup=lambda: self.docker_complete(), error=lambda e: self.docker_error(e))
        except:
            host.terminate()
            self.runner.remove_host(host)
            raise
        self.docker_host = host
        return host

    def docker_error(self, e):
        logger.error('Set %d docker error: %s' % (self.port_set, e))
        self.record_result(self.test_name, exception=e)
        self.docker_finalize()
        self.runner.target_set_error(self.port_set, e)

    def docker_finalize(self):
        if self.docker_host:
            self.runner.remove_host(self.docker_host)
            return_code = self.docker_host.terminate()
            self.docker_host = None
            self.docker_log.close()
            self.docker_log = None
            return return_code
        else:
            return None

    def docker_complete(self):
        self.state_transition(self.READY_STATE, self.TESTING_STATE)
        try:
            error_code = self.docker_finalize()
            exception = None
        except Exception as e:
            error_code = -1
            exception = e
        logger.debug("Set %d docker complete, return=%d (%s)" % (self.port_set, error_code, exception))
        self.record_result(self.test_name, code=error_code, exception=exception)
        if error_code:
            logger.info("Set %d FAILED test %s with error %s: %s" %
                         (self.port_set, self.test_name, error_code, exception))
        else:
            logger.info("Set %d PASSED test %s" % (self.port_set, self.test_name))
        self.run_next_test()

    def record_result(self, name, **kwargs):
        current = int(time.time())
        if name != self.test_name:
            logger.debug('Set %d starting test %s at %d' % (self.port_set, self.test_name, current))
            self.test_name = name
            self.test_start = current
        result = {
            'name': name,
            'runid': self.run_id,
            'started': self.test_start,
            'timestamp': current,
            'port': self.port_set
        }
        for arg in kwargs:
            result[arg] = None if kwargs[arg] == None else str(kwargs[arg])
        self.results[name] = result
        self.runner.gcp.publish_message('daq_runner', result)
