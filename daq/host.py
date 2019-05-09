"""Represent a device-under-test"""

import datetime
import logging
import os
import shutil
import time

from clib import tcpdump_helper

import configurator
import docker_test
import gcp
import report

LOGGER = logging.getLogger('host')


class _STATE:
    """Host state enum for testing cycle"""
    ERROR = 'Error condition'
    READY = 'Ready but not initialized'
    INIT = 'Initialization'
    WAITING = 'Waiting for activation'
    BASE = 'Baseline tests'
    MONITOR = 'Network monitor'
    NEXT = 'Ready for next'
    TESTING = 'Active test'
    DONE = 'Done with sequence'
    TERM = 'Host terminated'


def pre_states():
    """Return pre-test states for basic operation"""
    return ['startup', 'sanity', 'dhcp', 'base', 'monitor']


def post_states():
    """Return post-test states for recording finalization"""
    return ['finish', 'info', 'timer']


class ConnectedHost:
    """Class managing a device-under-test"""

    _MONITOR_SCAN_SEC = 30
    _STARTUP_MIN_TIME_SEC = 5
    _INST_DIR = "inst/"
    _DEVICE_PATH = "device/%s"
    _FAIL_BASE_FORMAT = "inst/fail_%s"
    _MODULE_CONFIG = "module_config.json"
    _CONTROL_PATH = "control/port-%s"
    _CORE_TESTS = ['pass', 'fail', 'ping']

    def __init__(self, runner, gateway, target, config):
        self.runner = runner
        self._gcp = runner.gcp
        self.gateway = gateway
        self.config = config
        self.target_port = target['port']
        self.target_mac = target['mac']
        self.fake_target = target['fake']
        self.devdir = self._init_devdir()
        self.run_id = self.make_runid()
        self.scan_base = os.path.abspath(os.path.join(self.devdir, 'scans'))
        self._port_base = self._get_port_base()
        self._device_base = self._get_device_base(config, self.target_mac)
        self.state = None
        self.no_test = config.get('no_test', False)
        self._state_transition(_STATE.READY)
        self.results = {}
        self.dummy = None
        self.running_test = None
        self.test_name = None
        self.test_start = None
        self.test_host = None
        self.test_port = None
        self._startup_time = None
        self._monitor_scan_sec = int(config.get('monitor_scan_sec', self._MONITOR_SCAN_SEC))
        self._fail_hook = config.get('fail_hook')
        self._mirror_intf_name = None
        self._tcp_monitor = None
        self.target_ip = None
        self._loaded_config = None
        self.reload_config()
        assert self._loaded_config, 'config was not loaded'
        self.remaining_tests = self._get_enabled_tests()

        self.record_result('startup', state='prep')
        self._record_result('info', state=self.target_mac, config=self._make_config_bundle())
        self._report = report.ReportGenerator(config, self._INST_DIR, self.target_mac,
                                              self._loaded_config)

    @staticmethod
    def make_runid():
        """Create a timestamped runid"""
        return '%06x' % int(time.time())

    def _init_devdir(self):
        devdir = os.path.join(self._INST_DIR, 'run-port-%02d' % self.target_port)
        shutil.rmtree(devdir, ignore_errors=True)
        os.makedirs(devdir)
        return devdir

    def _get_port_base(self):
        test_config = self.config.get('test_config')
        if not test_config:
            return None
        conf_base = os.path.abspath(os.path.join(test_config, 'port-%02d' % self.target_port))
        if not os.path.isdir(conf_base):
            LOGGER.warning('Test config directory not found: %s', conf_base)
            return None
        return conf_base

    def _make_config_bundle(self, config=None):
        return {
            'config': config if config else self._loaded_config,
            'timestamp': gcp.get_timestamp()
        }

    def _make_control_bundle(self):
        return {
            'paused': self.state == _STATE.READY
        }

    def _test_enabled(self, test):
        test_module = self._loaded_config['modules'].get(test)
        return test in self._CORE_TESTS or test_module and test_module.get('enabled', True)

    def _get_enabled_tests(self):
        return list(filter(self._test_enabled, self.config.get('test_list')))

    @staticmethod
    def _get_device_base(config, target_mac):
        """Get the base config path for a host device"""
        dev_base = config.get('site_path')
        if not dev_base:
            return None
        clean_mac = target_mac.replace(':', '')
        dev_path = os.path.abspath(os.path.join(dev_base, 'mac_addrs', clean_mac))
        if not os.path.isdir(dev_path):
            LOGGER.warning('Device config dir not found: %s', dev_path)
        return dev_path

    def initialize(self):
        """Fully initialize a new host set"""
        LOGGER.info('Target port %d initializing...', self.target_port)
        # There is a race condition here with ovs assigning ports, so wait a bit.
        time.sleep(2)
        shutil.rmtree(self.devdir, ignore_errors=True)
        os.makedirs(self.scan_base)
        self._initialize_config()
        network = self.runner.network
        self._mirror_intf_name = network.create_mirror_interface(self.target_port)
        if self.no_test:
            assert self.is_holding(), 'state is not holding'
            self.record_result('startup', state='hold')
        else:
            self._start_run()

    def _start_run(self):
        self._state_transition(_STATE.INIT, _STATE.READY)
        self._mark_skipped_tests()
        self.record_result('startup', state='go', config=self._make_config_bundle())
        self.record_result('sanity', state='run')
        self._startup_scan()

    def _mark_skipped_tests(self):
        for test in self.config['test_list']:
            if not self._test_enabled(test):
                self._record_result(test, state='skip')

    def _state_transition(self, target, expected=None):
        if expected is not None:
            message = 'state was %s expected %s' % (self.state, expected)
            assert self.state == expected, message
        LOGGER.debug('Target port %d state: %s -> %s', self.target_port, self.state, target)
        self.state = target

    def is_running(self):
        """Return True if this host is running active test."""
        return self.state != _STATE.ERROR and self.state != _STATE.DONE

    def is_holding(self):
        """Return True if this host paused and waiting to run."""
        return self.state == _STATE.READY

    def notify_activate(self):
        """Return True if ready to be activated in response to a DHCP notification."""
        if self.state == _STATE.READY:
            self._record_result('startup', state='hold')
        return self.state == _STATE.WAITING

    def _prepare(self):
        LOGGER.info('Target port %d waiting for dhcp as %s', self.target_port, self.target_mac)
        self._state_transition(_STATE.WAITING, _STATE.INIT)
        self.record_result('sanity', state='pass')
        self.record_result('dhcp', state='run')

    def terminate(self, trigger=True):
        """Terminate this host"""
        LOGGER.info('Target port %d terminate, trigger %s', self.target_port, trigger)
        self._release_config()
        self._state_transition(_STATE.TERM)
        self.record_result(self.test_name, state='terminate')
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
            self._prepare()
        elif self.state == _STATE.BASE:
            self._base_start()

    def trigger_ready(self):
        """Check if this host is ready to be triggered"""
        if self.state != _STATE.WAITING:
            return False
        timedelta = datetime.datetime.now() - self._startup_time
        if timedelta < datetime.timedelta(seconds=self._STARTUP_MIN_TIME_SEC):
            return False
        return True

    def trigger(self, state, target_ip=None, exception=None, delta_sec=-1):
        """Handle completion of DHCP subtask"""
        trigger_path = os.path.join(self.scan_base, 'dhcp_triggers.txt')
        with open(trigger_path, 'a') as output_stream:
            output_stream.write('%s %s %d\n' % (target_ip, state, delta_sec))
        if self.target_ip:
            LOGGER.debug('Target port %d already triggered', self.target_port)
            assert self.target_ip == target_ip, "target_ip mismatch"
            return True
        if not self.trigger_ready():
            LOGGER.warning('Target port %d ignoring premature trigger', self.target_port)
            return False
        self.target_ip = target_ip
        self._record_result('info', state='%s/%s' % (self.target_mac, target_ip))
        self.record_result('dhcp', ip=target_ip, state=state, exception=exception)
        if exception:
            self._state_transition(_STATE.ERROR)
            self.runner.target_set_error(self.target_port, exception)
        else:
            LOGGER.info('Target port %d triggered as %s', self.target_port, target_ip)
            self._state_transition(_STATE.BASE, _STATE.WAITING)
        return True

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
        if not self._monitor_scan_sec:
            LOGGER.info('Target port %d skipping background scan', self.target_port)
            self._monitor_continue()
            return
        self.record_result('monitor', time=self._monitor_scan_sec, state='run')
        monitor_file = os.path.join(self.scan_base, 'monitor.pcap')
        LOGGER.info('Target port %d background scan for %ds',
                    self.target_port, self._monitor_scan_sec)
        network = self.runner.network
        tcp_filter = ''
        intf_name = self._mirror_intf_name
        assert not self._tcp_monitor, 'tcp_monitor already active'
        LOGGER.debug('Target port %d background scan intf %s filter %s output in %s',
                     self.target_port, intf_name, tcp_filter, monitor_file)
        helper = tcpdump_helper.TcpdumpHelper(network.pri, tcp_filter, packets=None,
                                              intf_name=intf_name,
                                              timeout=self._monitor_scan_sec,
                                              pcap_out=monitor_file, blocking=False)
        self._tcp_monitor = helper
        self.runner.monitor_stream('tcpdump', self._tcp_monitor.stream(),
                                   self._tcp_monitor.next_line, hangup=self._monitor_complete,
                                   error=self._monitor_error)

    def _monitor_complete(self):
        LOGGER.info('Target port %d scan complete', self.target_port)
        self._monitor_cleanup(forget=False)
        self.record_result('monitor', state='pass')
        self._monitor_continue()

    def _monitor_continue(self):
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
        self.record_result('base', state='pass')
        return True

    def _run_next_test(self):
        try:
            if self.remaining_tests:
                self._docker_test(self.remaining_tests.pop(0))
            else:
                LOGGER.info('Target port %d no more tests remaining', self.target_port)
                self._state_transition(_STATE.DONE, _STATE.NEXT)
                self._report.finalize()
                self._gcp.upload_report(self._report.path)
                self.record_result('finish', state='done', report=self._report.path)
                self._report = None
                self.record_result(None)
        except Exception as e:
            LOGGER.error('Target port %d start error: %s', self.target_port, e)
            self._state_transition(_STATE.ERROR)
            self.runner.target_set_error(self.target_port, e)

    def _docker_test(self, test_name):
        self._state_transition(_STATE.TESTING, _STATE.NEXT)
        self.record_result(test_name, state='run')
        params = {
            'target_ip': self.target_ip,
            'target_mac': self.target_mac,
            'gateway_ip': self.gateway.IP(),
            'gateway_mac': self.gateway.MAC(),
            'conf_base': self._port_base,
            'dev_base': self._device_base,
            'scan_base': self.scan_base
        }

        self.test_host = docker_test.DockerTest(self.runner, self.target_port, self.devdir,
                                                test_name)
        self.test_port = self.runner.allocate_test_port(self.target_port)
        host_name = self.test_host.host_name if self.test_host else 'unknown'
        if 'ext_loip' in self.config:
            ext_loip = self.config['ext_loip'].replace('@', '%d')
            params['local_ip'] = ext_loip % self.test_port
            params['switch_ip'] = self.config['ext_addr']
            params['switch_port'] = str(self.target_port)
        LOGGER.debug('test_host start %s/%s', self.test_name, host_name)
        self._set_module_config(test_name, self._loaded_config)
        self.test_host.start(self.test_port, params, self._docker_callback)

    def _host_name(self):
        return self.test_host.host_name if self.test_host else 'unknown'

    def _host_dir_path(self):
        return os.path.join(self.devdir, 'nodes', self._host_name())

    def _host_tmp_path(self):
        return os.path.join(self._host_dir_path(), 'tmp')

    def _docker_callback(self, return_code=None, exception=None):
        host_name = self._host_name()
        LOGGER.info('test_host callback %s/%s was %s with %s',
                    self.test_name, host_name, return_code, exception)
        failed = return_code or exception
        if failed and self._fail_hook:
            fail_file = self._FAIL_BASE_FORMAT % host_name
            LOGGER.warning('Executing fail_hook: %s %s', self._fail_hook, fail_file)
            os.system('%s %s 2>&1 > %s.out' % (self._fail_hook, fail_file, fail_file))
        state = 'fail' if failed else 'pass'
        self.record_result(self.test_name, state=state, code=return_code, exception=exception)
        result_path = os.path.join(self._host_dir_path(), 'return_code.txt')
        try:
            with open(result_path, 'a') as output_stream:
                output_stream.write(str(return_code) + '\n')
        except Exception as e:
            LOGGER.error('While writing result code: %s', e)
        report_path = os.path.join(self._host_tmp_path(), 'report.txt')
        if os.path.isfile(report_path):
            self._report.accumulate(self.test_name, report_path)
        self.test_host = None
        self.runner.release_test_port(self.target_port, self.test_port)
        if exception:
            self._state_transition(_STATE.ERROR)
            self.runner.target_set_error(self.target_port, exception)
        else:
            self._state_transition(_STATE.NEXT, _STATE.TESTING)
            self._run_next_test()

    def _set_module_config(self, name, loaded_config):
        tmp_dir = self._host_tmp_path()
        configurator.write_config(tmp_dir, self._MODULE_CONFIG, loaded_config)
        self._record_result(name, config=self._loaded_config)

    def _merge_run_info(self, config):
        config['run_info'] = {
            'run_id': self.run_id,
            'mac_addr': self.target_mac,
            'daq_version': self.runner.version,
            'started': gcp.get_timestamp()
        }

    def _load_module_config(self, run_info=True):
        config = self.runner.get_base_config()
        if run_info:
            self._merge_run_info(config)
        configurator.load_and_merge(config, self._device_base, self._MODULE_CONFIG)
        configurator.load_and_merge(config, self._port_base, self._MODULE_CONFIG)
        return config

    def record_result(self, name, **kwargs):
        """Record a named result for this test"""
        current = gcp.get_timestamp()
        if name != self.test_name:
            LOGGER.debug('Target port %d report %s start %d',
                         self.target_port, name, current)
            self.test_name = name
            self.test_start = current
        if name:
            self._record_result(name, current, **kwargs)

    @staticmethod
    def clear_port(gcp_instance, port):
        """Clear the given port in the ui to a startup init state"""
        result = {
            'name': 'startup',
            'state': 'init',
            'runid': ConnectedHost.make_runid(),
            'timestamp': gcp.get_timestamp(),
            'port': port
        }
        gcp_instance.publish_message('daq_runner', 'test_result', result)

    def _record_result(self, name, run_info=True, current=None, **kwargs):
        result = {
            'name': name,
            'runid': (self.run_id if run_info else None),
            'device_id': self.target_mac,
            'started': self.test_start,
            'timestamp': current if current else gcp.get_timestamp(),
            'port': (self.target_port if run_info else None)
        }
        for arg in kwargs:
            result[arg] = None if kwargs[arg] is None else kwargs[arg]
        if result.get('exception'):
            result['exception'] = str(result['exception'])
        if name:
            self.results[name] = result
        self._gcp.publish_message('daq_runner', 'test_result', result)
        return result

    def _control_updated(self, control_config):
        LOGGER.info('Updated control config: %s %s', self.target_mac, control_config)
        paused = control_config.get('paused')
        if not paused and self.is_holding():
            self._start_run()
        elif paused and not self.is_holding():
            LOGGER.warning('Inconsistent control state for update of %s', self.target_mac)

    def reload_config(self):
        """Trigger a config reload due to an eternal config change."""
        holding = self.is_holding()
        new_config = self._load_module_config(run_info=holding)
        if holding:
            self._loaded_config = new_config
        config_bundle = self._make_config_bundle(new_config)
        LOGGER.info('Device config reloaded: %s %s', holding, self.target_mac)
        self._record_result(None, run_info=holding, config=config_bundle)
        return new_config

    def _dev_config_updated(self, dev_config):
        LOGGER.info('Device config update: %s %s', self.target_mac, dev_config)
        configurator.write_config(self._device_base, self._MODULE_CONFIG, dev_config)
        self.reload_config()

    def _initialize_config(self):
        dev_config = configurator.load_config(self._device_base, self._MODULE_CONFIG)
        self._gcp.register_config(self._DEVICE_PATH % self.target_mac,
                                  dev_config, self._dev_config_updated)
        self._gcp.register_config(self._CONTROL_PATH % self.target_port,
                                  self._make_control_bundle(),
                                  self._control_updated, immediate=True)
        self._record_result(None, config=self._make_config_bundle())

    def _release_config(self):
        self._gcp.release_config(self._DEVICE_PATH % self.target_mac)
        self._gcp.release_config(self._CONTROL_PATH % self.target_port)
