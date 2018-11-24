"""Represent a device-under-test"""

import datetime
import logging
import os
import shutil
import time

from clib import tcpdump_helper

import docker_test

LOGGER = logging.getLogger('host')


class _STATE():
    """Host state enum for testing cycle"""
    ERROR = 'Error condition'
    INIT = 'Initizalization'
    READY = 'Ready but not active'
    ACTIVE = 'Activated device'
    BASE = 'Baseline tests'
    MONITOR = 'Network monitor'
    NEXT = 'Ready for next'
    TESTING = 'Active test'
    DONE = 'Done with sequence'
    TERM = 'Host terminated'


class ConnectedHost():
    """Class managing a device-under-test"""

    _MONITOR_SCAN_SEC = 20
    _STARTUP_MIN_TIME_SEC = 5
    _REPORT_FORMAT = "report_%s_%s.txt"
    _TMPDIR_BASE = "inst"
    _REPORT_PREFIX = "\n#############"

    def __init__(self, runner, gateway, target, config):
        self.runner = runner
        self.gateway = gateway
        self.config = config
        self.target_port = target['port']
        self.target_mac = target['mac']
        self.fake_target = target['fake']
        self.tmpdir = self._initialize_tempdir()
        self.run_id = '%06x' % int(time.time())
        self.scan_base = os.path.abspath(os.path.join(self.tmpdir, 'scans'))
        self.state = None
        self.no_test = config.get('no_test', False)
        self._state_transition(_STATE.READY if self.no_test else _STATE.INIT)
        self.results = {}
        self.dummy = None
        self.running_test = None
        self.all_tests = config.get('test_list')
        self.remaining_tests = list(self.all_tests)
        self.test_name = None
        self.test_start = None
        self.test_host = None
        self.test_port = None
        self._mirror_intf_name = None
        self._tcp_monitor = None
        self.target_ip = None
        self.record_result('startup', state='run')
        self._report_path = None
        self._report_file = None
        self._initialize_report()
        self._startup_time = None

    def _initialize_tempdir(self):
        tmpdir = os.path.join(self._TMPDIR_BASE, 'run-port-%02d' % self.target_port)
        shutil.rmtree(tmpdir, ignore_errors=True)
        os.makedirs(tmpdir)
        return tmpdir

    def initialize(self):
        """Fully initialize a new host set"""
        LOGGER.info('Target port %d initializing...', self.target_port)
        # There is a race condition here with ovs assigning ports, so wait a bit.
        time.sleep(2)
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        os.makedirs(self.scan_base)
        network = self.runner.network
        self._mirror_intf_name = network.create_mirror_interface(self.target_port)
        if self.no_test:
            self.record_result('ready')
        else:
            self.record_result('startup')
            self.record_result('sanity', state='run')
            self._startup_scan()

    def get_tests(self):
        """Return a list of all expected tests for this host"""
        return ['startup', 'sanity', 'dhcp', 'base',
                'monitor'] + self.all_tests + ['finish', 'info', 'timer']

    def _state_transition(self, target, expected=None):
        if expected is not None:
            message = 'state was %s expected %s' % (self.state, expected)
            assert self.state == expected, message
        LOGGER.debug('Target port %d state: %s -> %s', self.target_port, self.state, target)
        self.state = target

    def is_active(self):
        """Return True if this host is still under active test."""
        LOGGER.debug('Target port %d is_active check state %s', self.target_port, self.state)
        return self.state != _STATE.ERROR and self.state != _STATE.DONE

    def _activate(self):
        LOGGER.info('Target port %d activating as %s', self.target_port, self.target_mac)

        self._state_transition(_STATE.ACTIVE, _STATE.INIT)
        self.record_result('sanity')
        self._push_record('info', state=self.target_mac)
        self.record_result('dhcp', state='run')

    def terminate(self, trigger=True):
        """Terminate this host"""
        LOGGER.info('Target port %d terminate, trigger %s', self.target_port, trigger)
        self._state_transition(_STATE.TERM)
        self.record_result(self.test_name, state='disconnect')
        self._monitor_cleanup()
        self.runner.network.delete_mirror_interface(self.target_port)
        if self.running_test:
            try:
                self.running_test.terminate()
                self.runner.remove_host(self.running_test)
                self.running_test = None
            except Exception as e:
                LOGGER.error('Target port %d terminating test: %s', self.target_port, e)
                LOGGER.exception(e)
        if trigger:
            self.runner.target_set_complete(self, 'Target port %d termination' % self.target_port)

    def idle_handler(self):
        """Trigger events from idle state"""
        if self.state == _STATE.INIT:
            self._activate()
        elif self.state == _STATE.BASE:
            self._base_start()

    def dhcp_result(self, state, target_ip=None, exception=None):
        """Handle completion of DHCP subtask"""
        if self.state != _STATE.ACTIVE:
            return
        timedelta = datetime.datetime.now() - self._startup_time
        if timedelta < datetime.timedelta(seconds=self._STARTUP_MIN_TIME_SEC):
            LOGGER.warning('Target port %d ignoring premature dhcp_result', self.target_port)
            return
        self.target_ip = target_ip
        self._push_record('info', state='%s/%s' % (self.target_mac, target_ip))
        self.record_result('dhcp', ip=target_ip, state=state, exception=exception)
        if exception:
            self._state_transition(_STATE.ERROR, _STATE.ACTIVE)
            self.runner.target_set_error(self.target_port, exception)
        else:
            LOGGER.info('Target port %d dhcp_result %s', self.target_port, target_ip)
            self._state_transition(_STATE.BASE, _STATE.ACTIVE)

    def _ping_test(self, src, dst, src_addr=None):
        if not src or not dst:
            LOGGER.error('Invalid ping test params, src=%s, dst=%s', src, dst)
            return False
        return self.runner.ping_test(src, dst, src_addr=src_addr)

    def _startup_scan(self):
        assert not self._tcp_monitor, 'tcp_monitor already active'
        startup_file = os.path.join(self.scan_base, 'startup.pcap')
        self._startup_time = datetime.datetime.now()
        LOGGER.info('Target port %d startup pcap capture', self.target_port)
        network = self.runner.network
        tcp_filter = ''
        LOGGER.debug('Target port %d startup scan intf %s filter %s output in %s',
                     self.target_port, self._mirror_intf_name, tcp_filter, startup_file)
        helper = tcpdump_helper.TcpdumpHelper(network.pri, tcp_filter, packets=None,
                                              intf_name=self._mirror_intf_name,
                                              timeout=None, pcap_out=startup_file, blocking=False)
        self._tcp_monitor = helper
        hangup = lambda: self._monitor_error(Exception('startup scan hangup'))
        self.runner.monitor_stream('tcpdump', self._tcp_monitor.stream(),
                                   self._tcp_monitor.next_line,
                                   hangup=hangup, error=self._monitor_error)

    def _base_start(self):
        try:
            success = self._base_tests()
            self._monitor_cleanup()
            if not success:
                LOGGER.warning('Target port %d base tests failed', self.target_port)
                self._state_transition(_STATE.ERROR)
                return
            LOGGER.info('Target port %d done with base.', self.target_port)
            self._monitor_scan()
        except Exception as e:
            self._monitor_cleanup()
            self._monitor_error(e)

    def _monitor_cleanup(self, forget=True):
        if self._tcp_monitor:
            LOGGER.info('Target port %d monitor scan complete', self.target_port)
            if forget:
                self.runner.monitor_forget(self._tcp_monitor.stream())
            self._tcp_monitor.terminate()
            self._tcp_monitor = None

    def _monitor_error(self, e):
        LOGGER.error('Target port %d monitor error: %s', self.target_port, e)
        self._monitor_cleanup(forget=False)
        self.record_result(self.test_name, exception=e)
        self._state_transition(_STATE.ERROR)
        self.runner.target_set_error(self.target_port, e)

    def _monitor_scan(self):
        self._state_transition(_STATE.MONITOR, _STATE.BASE)
        self.record_result('monitor', time=self._MONITOR_SCAN_SEC, state='run')
        monitor_file = os.path.join(self.scan_base, 'monitor.pcap')
        LOGGER.info('Target port %d background scan for %d seconds...',
                    self.target_port, self._MONITOR_SCAN_SEC)
        network = self.runner.network
        tcp_filter = ''
        intf_name = self._mirror_intf_name
        assert not self._tcp_monitor, 'tcp_monitor already active'
        LOGGER.debug('Target port %d background scan intf %s filter %s output in %s',
                     self.target_port, intf_name, tcp_filter, monitor_file)
        helper = tcpdump_helper.TcpdumpHelper(network.pri, tcp_filter, packets=None,
                                              intf_name=intf_name,
                                              timeout=self._MONITOR_SCAN_SEC,
                                              pcap_out=monitor_file, blocking=False)
        self._tcp_monitor = helper
        self.runner.monitor_stream('tcpdump', self._tcp_monitor.stream(),
                                   self._tcp_monitor.next_line, hangup=self._monitor_complete,
                                   error=self._monitor_error)

    def _monitor_complete(self):
        LOGGER.info('Target port %d scan complete', self.target_port)
        self._monitor_cleanup(forget=False)
        self.record_result('monitor')
        self._state_transition(_STATE.NEXT, _STATE.MONITOR)
        self._run_next_test()

    def _base_tests(self):
        self.record_result('base', state='run')
        if not self._ping_test(self.gateway, self.target_ip):
            LOGGER.debug('Target port %d warmup ping failed', self.target_port)
        try:
            success1 = self._ping_test(self.gateway, self.target_ip), 'simple ping failed'
            success2 = self._ping_test(self.gateway, self.target_ip,
                                       src_addr=self.fake_target), 'target ping failed'
            if not success1 or not success2:
                return False
        except Exception as e:
            self.record_result('base', exception=e)
            self._monitor_cleanup()
            raise
        self.record_result('base')
        return True

    def _run_next_test(self):
        try:
            if self.remaining_tests:
                self._docker_test(self.remaining_tests.pop(0))
            else:
                LOGGER.info('Target port %d no more tests remaining', self.target_port)
                self._state_transition(_STATE.DONE, _STATE.NEXT)
                self._finalize_report()
                self.record_result('finish', report=self._report_path)
                self.record_result(None)
        except Exception as e:
            LOGGER.error('Target port %d start error: %s', self.target_port, e)
            self._state_transition(_STATE.ERROR)
            self.runner.target_set_error(self.target_port, e)

    def _initialize_report(self):
        report_timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
        report_filename = self._REPORT_FORMAT % (self.target_mac.replace(':', ''),
                                                 report_timestamp)
        report_path = os.path.join(self._TMPDIR_BASE, report_filename)

        LOGGER.info('Creating report as %s', report_path)
        self._report_path = report_path
        self._report_file = open(report_path, "w")
        self._report_file.write('DAQ scan report for device %s\n' % self.target_mac)

    def _report_write(self, msg):
        self._report_file.write('%s %s\n' % (self._REPORT_PREFIX, msg))

    def _finalize_report(self):
        LOGGER.info('Finalizing report %s', self._report_path)
        self._report_write('Report complete.')
        self._report_file.close()
        self._report_file = None
        self.runner.gcp.upload_report(self._report_path)

    def _docker_test(self, test_name):
        self._state_transition(_STATE.TESTING, _STATE.NEXT)
        self.record_result(test_name, state='run')
        params = {
            'target_ip': self.target_ip,
            'target_mac': self.target_mac,
            'gateway_ip': self.gateway.IP(),
            'gateway_mac': self.gateway.MAC(),
            'scan_base': self.scan_base
        }
        self.test_host = docker_test.DockerTest(self.runner, self, test_name)
        self.test_port = self.runner.allocate_test_port(self.target_port)
        host_name = self.test_host.host_name if self.test_host else 'unknown'
        LOGGER.debug('test_host start %s/%s', self.test_name, host_name)
        self.test_host.start(self.test_port, params, self._docker_callback)

    def _docker_callback(self, return_code=None, exception=None):
        host_name = self.test_host.host_name if self.test_host else 'unknown'
        LOGGER.debug('test_host callback %s/%s was %s with %s',
                     self.test_name, host_name, return_code, exception)
        self.record_result(self.test_name, code=return_code, exception=exception)
        result_path = os.path.join(self.tmpdir, 'nodes', host_name, 'return_code.txt')
        try:
            with open(result_path, 'a') as output_stream:
                output_stream.write(str(return_code))
        except Exception as e:
            LOGGER.error('While writing result code: %s', e)
        report_path = os.path.join(self.tmpdir, 'nodes', host_name, 'tmp', 'report.txt')
        if os.path.isfile(report_path):
            self._report_write('Report for test %s' % self.test_name)
            with open(report_path, 'r') as report_stream:
                shutil.copyfileobj(report_stream, self._report_file)
        self.test_host = None
        self.runner.release_test_port(self.target_port, self.test_port)
        if exception:
            self._state_transition(_STATE.ERROR)
            self.runner.target_set_error(self.target_port, exception)
        else:
            self._state_transition(_STATE.NEXT, _STATE.TESTING)
            self._run_next_test()

    def record_result(self, name, **kwargs):
        """Record a named result for this test"""
        current = int(time.time())
        if name != self.test_name:
            LOGGER.debug('Target port %d report %s start %d',
                         self.target_port, name, current)
            self.test_name = name
            self.test_start = current
        if name:
            self._push_record(name, current, **kwargs)

    def _push_record(self, name, current=None, **kwargs):
        if not current:
            current = int(time.time())
        result = {
            'name': name,
            'runid': self.run_id,
            'started': self.test_start,
            'timestamp': current,
            'port': self.target_port
        }
        for arg in kwargs:
            result[arg] = None if kwargs[arg] is None else str(kwargs[arg])
        self.results[name] = result
        self.runner.gcp.publish_message('daq_runner', result)
