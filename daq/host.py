"""Represent a device-under-test"""

import logging
import os
import random
import shutil
import time
import traceback

from clib import docker_host
from clib import tcpdump_helper

import dhcp_monitor
import docker_test

LOGGER = logging.getLogger('host')


class _STATE(object):
    """Host state enum for testing cycle"""
    ERROR = 'Error condition'
    INIT = 'Initizalization'
    STARTUP = 'Startup sequence'
    ACTIVE = 'Active device'
    DHCP = 'DHCP scan'
    BASE = 'Baseline tests'
    MONITOR = 'Network monitor'
    READY = 'Ready for next'
    TESTING = 'Active test'
    DONE = 'Done with sequence'


class ConnectedHost(object):
    """Class managing a device-under-test"""

    NETWORKING_OFFSET = 0
    DUMMY_OFFSET = 1
    TEST_OFFSET = 2

    TEST_IP_FORMAT = '192.168.84.%d'
    MONITOR_SCAN_SEC = 20

    TEST_LIST = ['pass', 'fail', 'ping', 'bacnet', 'nmap', 'mudgee']
    TEST_ORDER = ['startup', 'sanity', 'dhcp', 'base',
                  'monitor'] + TEST_LIST + ['finish', 'info', 'timer']

    def __init__(self, runner, port_set, config):
        self.runner = runner
        self.config = config
        self.port_set = port_set
        self.pri_base = port_set * 10
        self.tmpdir = os.path.join('inst', 'run-port-%02d' % self.port_set)
        self.run_id = '%06x' % int(time.time())
        self.scan_base = os.path.abspath(os.path.join(self.tmpdir, 'scans'))
        self.state = None
        self._state_transition(_STATE.INIT)
        self.results = {}
        self.dummy = None
        self.running_test = None
        self.remaining_tests = list(self.TEST_LIST)
        self.test_name = None
        self.test_start = None
        self.tcp_monitor = None
        self.fake_target = None
        self.dhcp_monitor = None
        self.target_ip = None
        self.target_mac = None
        self.networking = None
        self.record_result('startup', state='run')

    def initialize(self):
        """Fully initialize a new host set"""
        LOGGER.info('Set %d initializing...', self.port_set)
        # There is a race condition here with ovs assigning ports, so wait a bit.
        time.sleep(2)
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        networking_name = 'gw%02d' % self.port_set
        networking_port = self.pri_base + self.NETWORKING_OFFSET
        LOGGER.debug("Adding networking host on port %d", networking_port)
        cls = docker_host.make_docker_host('daq/networking', prefix='daq', network='bridge')
        try:
            self.networking = self.runner.add_host(networking_name, port=networking_port,
                                                   cls=cls, tmpdir=self.tmpdir)
            self._create_config(self.networking.tmpdir)
            self.record_result('startup')
        except Exception as e:
            self._state_transition(_STATE.ERROR)
            self.record_result('startup', exception=e)

    def _create_config(self, parent_dir):
        config_path = self.config.get('config_path')
        if config_path:
            target_dir = os.path.join(parent_dir, 'tmp', 'public')
            os.makedirs(target_dir)
            target_path = os.path.join(target_dir, 'config.json')
            shutil.copyfile(config_path, target_path)
            LOGGER.info('Copied config file to %s', target_path)

    def _state_transition(self, target, expected=None):
        if expected is not None:
            message = 'state was %s expected %s' % (self.state, expected)
            assert self.state == expected, message
        LOGGER.debug('Set %d state %s -> %s', self.port_set, self.state, target)
        self.state = target

    def is_active(self):
        """Return True if this host is still under active test."""
        LOGGER.debug('Set %d is_active check state %s', self.port_set, self.state)
        return self.state != _STATE.ERROR and self.state != _STATE.DONE

    def _activate(self):
        self._state_transition(_STATE.STARTUP, _STATE.INIT)
        LOGGER.info('Set %d activating.', self.port_set)

        if not os.path.exists(self.scan_base):
            os.makedirs(self.scan_base)

        try:
            self.record_result('sanity', state='run')
            networking = self.networking
            networking.activate()
            self._startup_scan()

            dummy_name = 'dummy%02d' % self.port_set
            dummy_port = self.pri_base + self.DUMMY_OFFSET
            self.dummy = self.runner.add_host(dummy_name, port=dummy_port)
            dummy = self.dummy

            self.fake_target = self.TEST_IP_FORMAT % random.randint(10, 99)
            LOGGER.debug('Adding fake target at %s', self.fake_target)
            intf = self.runner.get_host_interface(networking)
            networking.cmd('ip addr add %s dev %s' % (self.fake_target, intf))

            # Dummy doesn't use DHCP, so need to set default route manually.
            dummy.cmd('route add -net 0.0.0.0 gw %s' % networking.IP())

            self.dhcp_monitor = dhcp_monitor.DhcpMonitor(self.runner, self.port_set,
                                                         networking, self.dhcp_callback)

            assert self._ping_test(networking, dummy), 'ping failed'
            assert self._ping_test(dummy, networking), 'ping failed'
            assert self._ping_test(dummy, self.fake_target), 'ping failed'
            assert self._ping_test(networking, dummy, src_addr=self.fake_target), 'ping failed'
            self.record_result('sanity')
            self._state_transition(_STATE.ACTIVE, _STATE.STARTUP)
        except Exception as e:
            LOGGER.error('Set %d sanity error: %s', self.port_set, e)
            LOGGER.exception(e)
            self.record_result('sanity', exception=e)
            self._state_transition(_STATE.ERROR)

    def terminate(self, trigger=True, removed=False):
        """Terminate this host"""
        LOGGER.info('Set %d terminate, trigger %s, removed %s', self.port_set, trigger, removed)
        if not removed and self.config.get('result_linger', False):
            LOGGER.error('Unexpected terminate with linger')
            traceback.print_stack()
        self._state_transition(_STATE.ERROR)
        if self.dhcp_monitor:
            self.dhcp_monitor.cleanup()
        self._monitor_cleanup()
        if self.networking:
            try:
                self.networking.terminate()
                self.runner.remove_host(self.networking)
                self.networking = None
            except Exception as e:
                LOGGER.error('Set %d terminating networking: %s', self.port_set, e)
                LOGGER.exception(e)
        if self.dummy:
            try:
                self.dummy.terminate()
                self.runner.remove_host(self.dummy)
                self.dummy = None
            except Exception as e:
                LOGGER.error('Set %d terminating dummy: %s', self.port_set, e)
                LOGGER.exception(e)
        if self.running_test:
            try:
                self.running_test.terminate()
                self.runner.remove_host(self.running_test)
                self.running_test = None
            except Exception as e:
                LOGGER.error('Set %d terminating test: %s', self.port_set, e)
                LOGGER.exception(e)
        if trigger:
            self.runner.target_set_complete(self)

    def idle_handler(self):
        """Trigger events from idle state"""
        if self.state == _STATE.INIT:
            self._activate()
        elif self.state == _STATE.ACTIVE:
            self._state_transition(_STATE.DHCP, _STATE.ACTIVE)
            self.record_result('dhcp', state='run')
            self.dhcp_monitor.start()
        elif self.state == _STATE.BASE:
            self._base_start()

    def dhcp_callback(self, state, target_mac=None, target_ip=None, exception=None):
        """Handle completion of DHCP subtask"""
        self.record_result('dhcp', info=target_mac, ip=target_ip, state=state, exception=exception)
        self.target_mac = target_mac
        self.target_ip = target_ip
        if exception:
            self._state_transition(_STATE.ERROR, _STATE.DHCP)
            self.runner.target_set_error(self.port_set, exception)
        else:
            self._state_transition(_STATE.BASE, _STATE.DHCP)

    def _ping_test(self, src, dst, src_addr=None):
        dst_name = dst if isinstance(dst, str) else dst.name
        dst_ip = dst if isinstance(dst, str) else dst.IP()
        from_msg = ' from %s' % src_addr if src_addr else ''
        LOGGER.info("Set %d ping test %s->%s%s", self.port_set, src.name, dst_name, from_msg)
        failure = "ping FAILED"
        assert dst_ip != "0.0.0.0", "IP address not assigned, can't ping"
        ping_opt = '-I %s' % src_addr if src_addr else ''
        try:
            output = src.cmd('ping -c2', ping_opt, dst_ip, '> /dev/null 2>&1 || echo ', failure)
            return output.strip() != failure
        except Exception as e:
            LOGGER.info('Set %d ping failure: %s', self.port_set, e)
            return False

    def _startup_scan(self):
        assert not self.tcp_monitor, 'tcp_monitor already active'
        LOGGER.debug('Set %d startup pcap start', self.port_set)
        startup_file = os.path.join('/tmp', 'startup.pcap')
        tcp_filter = ''
        helper = tcpdump_helper.TcpdumpHelper(self.networking, tcp_filter, packets=None,
                                              timeout=None, pcap_out=startup_file, blocking=False)
        self.tcp_monitor = helper
        hangup = lambda: self._monitor_error(Exception('startup scan hangup'))
        self.runner.monitor_stream('tcpdump', self.tcp_monitor.stream(),
                                   self.tcp_monitor.next_line,
                                   hangup=hangup, error=self._monitor_error)

    def _base_start(self):
        try:
            self._base_tests()
            self._monitor_cleanup()
            LOGGER.info('Set %d done with base.', self.port_set)
            self._monitor_scan()
        except Exception as e:
            self._monitor_cleanup()
            self._monitor_error(e)

    def _monitor_cleanup(self, forget=True):
        if self.tcp_monitor:
            LOGGER.debug('Set %d monitor scan cleanup (forget=%s)', self.port_set, forget)
            if forget:
                self.runner.monitor_forget(self.tcp_monitor.stream())
            self.tcp_monitor.terminate()
            self.tcp_monitor = None

    def _monitor_error(self, e):
        LOGGER.error('Set %d monitor error: %s', self.port_set, e)
        self._monitor_cleanup(forget=False)
        self.record_result(self.test_name, exception=e)
        self._state_transition(_STATE.ERROR)
        self.runner.target_set_error(self.port_set, e)

    def _monitor_scan(self):
        self._state_transition(_STATE.MONITOR, _STATE.BASE)
        self.record_result('monitor', time=self.MONITOR_SCAN_SEC, state='run')
        LOGGER.info('Set %d background scan for %d seconds...',
                    self.port_set, self.MONITOR_SCAN_SEC)
        network = self.runner.network
        intf_name = network.sec_name
        monitor_file = os.path.join(self.scan_base, 'monitor.pcap')
        tcp_filter = 'vlan %d' % self.pri_base
        assert not self.tcp_monitor, 'tcp_monitor already active'
        helper = tcpdump_helper.TcpdumpHelper(network.pri, tcp_filter, packets=None,
                                              intf_name=intf_name,
                                              timeout=self.MONITOR_SCAN_SEC,
                                              pcap_out=monitor_file, blocking=False)
        self.tcp_monitor = helper
        self.runner.monitor_stream('tcpdump', self.tcp_monitor.stream(),
                                   self.tcp_monitor.next_line, hangup=self._monitor_complete,
                                   error=self._monitor_error)

    def _monitor_complete(self):
        LOGGER.info('Set %d monitor scan complete', self.port_set)
        self._monitor_cleanup(forget=False)
        self.record_result('monitor')
        self._state_transition(_STATE.READY, _STATE.MONITOR)
        self._run_next_test()

    def _base_tests(self):
        self.record_result('base', state='run')
        if not self._ping_test(self.networking, self.target_ip):
            LOGGER.debug('Set %d warmup ping failed', self.port_set)
        try:
            assert self._ping_test(self.networking, self.target_ip), 'simple ping failed'
            assert self._ping_test(self.networking, self.target_ip,
                                   src_addr=self.fake_target), 'target ping failed'
        except:
            self._monitor_cleanup()
            raise
        self.record_result('base')

    def _run_next_test(self):
        if self.remaining_tests:
            self._docker_test(self.remaining_tests.pop(0))
        else:
            LOGGER.info('Set %d no more tests remaining', self.port_set)
            self._state_transition(_STATE.DONE, _STATE.READY)
            self.record_result('finish')

    def _docker_test(self, test_name):
        self._state_transition(_STATE.TESTING, _STATE.READY)
        self.record_result(test_name, state='run')
        port = self.pri_base + self.TEST_OFFSET
        params = {
            'target_ip': self.target_ip,
            'target_mac': self.target_mac,
            'gateway_ip': self.networking.IP(),
            'gateway_mac': self.networking.MAC(),
            'scan_base': self.scan_base
        }
        test = docker_test.DockerTest(self.runner, self, test_name)
        test.start(port, params, self._docker_callback)

    def _docker_callback(self, return_code=None, exception=None):
        self.record_result(self.test_name, exception=exception)
        self.record_result(self.test_name, code=return_code, exception=exception)
        if exception:
            self._state_transition(_STATE.ERROR)
            self.runner.target_set_error(self.port_set, exception)
        else:
            self._state_transition(_STATE.READY, _STATE.TESTING)
            self._run_next_test()

    def record_result(self, name, **kwargs):
        """Record a named result for this test"""
        current = int(time.time())
        if name != self.test_name:
            LOGGER.debug('Set %d starting test %s at %d', self.port_set, self.test_name, current)
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
            result[arg] = None if kwargs[arg] is None else str(kwargs[arg])
        self.results[name] = result
        self.runner.gcp.publish_message('daq_runner', result)
