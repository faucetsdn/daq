"""Represent a device-under-test"""

import functools
import os
import shutil
import time
from datetime import timedelta, datetime
from ipaddress import ip_network
import grpc

from clib import tcpdump_helper

from report import ResultType, ReportGenerator
from proto import usi_pb2 as usi
from proto import usi_pb2_grpc as usi_service
from proto.system_config_pb2 import DhcpMode

import configurator
from test_modules import DockerModule, IpAddrModule, NativeModule
from env import DAQ_RUN_DIR
import gcp
import logger

DEV_DIR_PREFIX = 'run-'

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
    HOLD = 'Holding with no test'
    TERM = 'Host terminated'



class MODE:
    """Test module modes for state reporting."""
    INIT = 'init'
    PREP = 'prep'
    HOLD = 'hold'
    CONF = 'conf'
    EXEC = 'exec'
    FINE = 'fine'
    NOPE = 'nope'
    DONE = 'done'
    TERM = 'term'
    LONG = 'long'
    MERR = 'merr'


def pre_states():
    """Return pre-test states for basic operation"""
    return ['startup', 'sanity', 'acquire', 'base', 'monitor']

def post_states():
    """Return post-test states for recording finalization"""
    return ['finish', 'info', 'timer']


def get_test_config(config, test):
    """Get a single test module's config"""
    return config["modules"].get(test)


class ConnectedHost:
    """Class managing a device-under-test"""

    _STARTUP_MIN_TIME_SEC = 5
    _RPC_TIMEOUT_SEC = 20
    _INST_DIR = DAQ_RUN_DIR
    _DEVICE_PATH = 'device/%s'
    _NETWORK_DIR = os.path.join(DAQ_RUN_DIR, 'network')
    _MODULE_CONFIG = 'module_config.json'
    _DEVICE_CONFIG = 'device_config.json'
    _TYPE_CONFIG = 'type_config.json'
    _PORT_CONFIG = 'port_config.json'
    _BASE_CONFIG = 'base_config.json'
    _CONTROL_PATH = 'control/port-%s'
    _AUX_DIR = 'aux/'
    _CONFIG_DIR = 'config/'
    _TIMEOUT_EXCEPTION = TimeoutError('Timeout expired')
    _PATH_PREFIX = os.path.abspath('.') + '/' + _INST_DIR

    # pylint: disable=too-many-statements
    def __init__(self, runner, device, config):
        self.configurator = configurator.Configurator()
        self.runner = runner
        self._gcp = runner.gcp
        self.gateway = device.gateway
        self.config = config
        self.switch_setup = self.config.get('switch_setup', {})
        self._no_test = self.config.get('no_test', False)
        self.device = device
        self.target_mac = device.mac
        self.target_port = device.port.port_no
        self.fake_target = self.gateway.fake_target
        self.devdir = self._init_devdir()
        self.run_id = self.make_runid()
        self.scan_base = os.path.abspath(os.path.join(self.devdir, 'scans'))
        self.logger = logger.get_logger('host')
        self._port_base = self._get_port_base()
        self._device_base = self._get_device_base()
        self.state = None
        self._state_transition(_STATE.READY)
        self.results = {}
        self.dummy = None
        self.test_name = None
        self.test_start = gcp.get_timestamp()
        self.test_host = None
        self.test_port = None
        self._startup_time = None
        self._monitor_scan_sec = int(config.get('monitor_scan_sec', 0))
        _default_timeout_sec = int(config.get('default_timeout_sec', 0))
        self._default_timeout_sec = _default_timeout_sec if _default_timeout_sec else None
        self._usi_config = config.get('usi_setup', {})
        self._topology_hook_script = config.get('topology_hook')
        self._mirror_intf_name = None
        self._monitor_ref = None
        self._monitor_start = None
        self.target_ip = None
        self._dhcp_listeners = []
        self._loaded_config = None
        self.reload_config()
        assert self._loaded_config, 'config was not loaded'
        self._write_module_config(self._loaded_config, self._device_aux_path())
        self.enabled_tests = self._get_enabled_tests()
        self.remaining_tests = list(self.enabled_tests)
        self.logger.info('Host %s running with enabled tests %s', self.target_mac,
                         self.remaining_tests)
        self._report = ReportGenerator(config, self.target_mac, self._loaded_config)
        self.record_result('startup', state=MODE.PREP)
        self._record_result('info', state=self.target_mac, config=self._make_config_bundle())
        self._trigger_path = None
        self._startup_file = None
        self.timeout_handler = self._aux_module_timeout_handler
        self._all_ips = []
        self._ip_listener = None

    @staticmethod
    def make_runid():
        """Create a timestamped runid"""
        return '%06x' % int(time.time())

    def _init_devdir(self):
        devdir = os.path.join(self._INST_DIR, DEV_DIR_PREFIX + self.target_mac.replace(':', ''))
        shutil.rmtree(devdir, ignore_errors=True)
        os.makedirs(devdir)
        return devdir

    def _get_port_base(self):
        test_config = self.config.get('test_config')
        if test_config and self.target_port:
            conf_base = os.path.abspath(os.path.join(test_config, 'port-%02d' % self.target_port))
            if not os.path.isdir(conf_base):
                self.logger.warning('Test config directory not found: %s', conf_base)
                return None
            return conf_base
        return None

    def _make_config_bundle(self, config=None):
        return {
            'config': config if config else self._loaded_config,
            'timestamp': gcp.get_timestamp()
        }

    def _make_control_bundle(self):
        return {
            'paused': self.state == _STATE.READY
        }

    def _get_test_config(self, test):
        return get_test_config(self._loaded_config, test)

    def _test_enabled(self, test):
        test_config = self._get_test_config(test) or {}
        return test_config.get('enabled', False)

    def _get_test_timeout(self, test):
        if test == 'hold':
            return None
        test_module = self._get_test_config(test)
        if not test_module:
            return self._default_timeout_sec
        return test_module.get('timeout_sec', self._default_timeout_sec)

    def get_port_flap_timeout(self, test):
        """Get port toggle timeout configuration that's specific to each test module"""
        test_module = self._get_test_config(test)
        if not test_module:
            return None
        return test_module.get('port_flap_timeout_sec')

    def _get_enabled_tests(self):
        return list(filter(self._test_enabled, self.config.get('test_list')))

    def _get_device_base(self):
        """Get the base config path for a host device"""
        site_path = self.config.get('site_path')
        if not site_path:
            return None
        clean_mac = self.target_mac.replace(':', '')
        dev_path = os.path.abspath(os.path.join(site_path, 'mac_addrs', clean_mac))
        if not os.path.isdir(dev_path):
            self._create_device_dir(dev_path)
        return dev_path

    def _get_static_ip(self):
        return self._loaded_config.get('static_ip')

    def _get_dhcp_mode(self):
        mode_str = self._loaded_config['modules'].get('ipaddr', {}).get('dhcp_mode', "NORMAL")
        return DhcpMode.Value(mode_str)

    def _get_unique_upload_path(self, file_name):
        base = os.path.basename(file_name)
        partial = os.path.join('tests', self.test_name, base) if self.test_name else base
        return os.path.join('run_id', self.run_id, partial)

    def _load_config(self, name, config, path, filename):
        if not path:
            return config
        if name:
            self.logger.info('Loading %s module config from %s/%s', name, path, filename)
        old_path = os.path.join(path, self._MODULE_CONFIG)
        if os.path.exists(old_path):
            raise Exception('Old %s config found in %s, should be renamed to %s' %
                            (name, old_path, filename))
        config_file = os.path.join(path, filename)
        if os.path.exists(config_file):
            return self.configurator.merge_config(config, os.path.join(path, filename))
        return config

    def _write_module_config(self, config, path):
        self.configurator.write_config(config, os.path.join(path, self._MODULE_CONFIG))

    def _type_path(self):
        dev_config = self._load_config(None, {}, self._device_base, self._DEVICE_CONFIG)
        device_type = dev_config.get('device_type')
        if not device_type:
            return None
        self.logger.info('Configuring device %s as type %s', self.device, device_type)
        site_path = self.config.get('site_path')
        type_path = os.path.abspath(os.path.join(site_path, 'device_types', device_type))
        return type_path

    def _type_aux_path(self):
        type_path = self._type_path()
        if not type_path:
            return None
        aux_path = os.path.join(type_path, self._AUX_DIR)
        if not os.path.exists(aux_path):
            self.logger.info('Skipping missing type dir %s', aux_path)
            return None
        return aux_path

    def _create_device_dir(self, path):
        self.logger.warning('Creating new device dir: %s', path)
        os.makedirs(path)
        template_dir = self.config.get('device_template')
        if not template_dir:
            self.logger.warning('Skipping defaults since no device_template found')
            return
        self.logger.info('Copying template files from %s to %s', template_dir, path)
        for file in os.listdir(template_dir):
            self.logger.info('Copying %s...', file)
            shutil.copy(os.path.join(template_dir, file), path)

    def _upload_file(self, path):
        upload_path = self._get_unique_upload_path(path)
        return self._gcp.upload_file(path, upload_path)

    def initialize(self):
        """Fully initialize a new host set"""
        self.logger.info('Target device %s initializing...', self)
        # There is a race condition here with ovs assigning ports, so wait a bit.
        time.sleep(2)
        shutil.rmtree(self.devdir, ignore_errors=True)
        os.makedirs(self.scan_base)
        self._initialize_config()
        network = self.runner.network
        if self.target_port:
            self._mirror_intf_name = network.create_mirror_interface(self.target_port)
        self._topology_hook()
        if self.config['test_list']:
            self._start_run()
        else:
            assert self.is_ready(), 'state is not holding'
            self.record_result('startup', state=MODE.HOLD)

    def _start_run(self):
        self._state_transition(_STATE.INIT, _STATE.READY)
        self._mark_skipped_tests()
        self.record_result('startup', state=MODE.DONE, config=self._make_config_bundle())
        self.record_result('sanity', state=MODE.EXEC)
        self._startup_scan()

    def _mark_skipped_tests(self):
        for test in self.config['test_list']:
            if not self._test_enabled(test):
                self._record_result(test, state=MODE.NOPE)

    def _state_transition(self, target, expected=None):
        if expected is not None:
            message = 'state was %s expected %s' % (self.state, expected)
            assert self.state == expected, message
        assert self.state != _STATE.TERM, 'host already terminated'
        self.logger.info('Target device %s state: %s -> %s', self, self.state, target)
        self.state = target

    def _build_switch_info(self) -> usi.SwitchInfo:
        switch_config = self._get_switch_config()
        model_str = switch_config['model']
        if model_str == 'FAUX_SWITCH' or not self.target_port:
            return None
        if model_str:
            switch_model = usi.SwitchModel.Value(model_str)
        else:
            switch_model = usi.SwitchModel.OVS_SWITCH
        params = {
            "ip_addr": switch_config["ip"],
            "device_port": self.target_port,
            "model": switch_model,
            "username": switch_config["username"],
            "password": switch_config["password"]
        }
        return usi.SwitchInfo(**params)

    def is_running(self):
        """Return True if this host is running active test."""
        return self.state not in (_STATE.ERROR, _STATE.DONE)

    def is_ready(self):
        """Return True if this host paused and waiting to run."""
        return self.state == _STATE.READY

    def notify_activate(self):
        """Return True if ready to be activated in response to an ip notification."""
        if self.state == _STATE.READY:
            self._record_result('startup', state=MODE.HOLD)
        return self.state == _STATE.WAITING

    def connect_port(self, connect):
        """Connects/Disconnects port for this host"""
        switch_info = self._build_switch_info()
        if not switch_info:
            self.logger.info('No switch model found, skipping port connect')
            return False
        try:
            with grpc.insecure_channel(self._usi_config.get('url')) as channel:
                timeout = self._usi_config.get('rpc_timeout_sec', self._RPC_TIMEOUT_SEC)
                stub = usi_service.USIServiceStub(channel)
                if connect:
                    res = stub.connect(switch_info, timeout=timeout)
                else:
                    res = stub.disconnect(switch_info, timeout=timeout)
                self.logger.info('Target port %s %s successful? %s', self.target_port, "connect"
                                 if connect else "disconnect", res.success)
        except Exception as e:
            self.logger.error(e)
            raise e
        return True

    def _prepare(self):
        self.logger.info('Target device %s waiting for ip', self)
        self._state_transition(_STATE.WAITING, _STATE.INIT)
        self.record_result('sanity', state=MODE.DONE)
        self.record_result('acquire', state=MODE.EXEC)
        static_ip = self._get_static_ip()
        if static_ip:
            self.logger.info('Target device %s using ip mode STATIC %s', self, static_ip)
            self.device.dhcp_mode = DhcpMode.STATIC_IP
            time.sleep(self._STARTUP_MIN_TIME_SEC)
            self.runner.ip_notify(MODE.NOPE, {
                'type': 'STATIC',
                'mac': self.target_mac,
                'ip': static_ip,
                'delta': -1
            }, self.gateway)
        else:
            if not self.device.dhcp_mode:
                dhcp_mode = self._get_dhcp_mode()
                self.device.dhcp_mode = dhcp_mode
            # enables dhcp response for this device
            wait_time = self.runner.config.get("long_dhcp_response_sec") \
                if self.device.dhcp_mode == DhcpMode.LONG_RESPONSE else 0
            self.logger.info('Target device %s ip mode %s, wait %s',
                             self, DhcpMode.Name(self.device.dhcp_mode), wait_time)
            if self.device.dhcp_mode == DhcpMode.EXTERNAL:
                self.timeout_handler = self._external_dhcp_timeout_handler
            else:
                self.gateway.change_dhcp_response_time(self.target_mac, wait_time)
        _ = [listener(self.device) for listener in self._dhcp_listeners]

    def _aux_module_timeout_handler(self):
        # clean up tcp monitor that could be open
        self._monitor_error(self._TIMEOUT_EXCEPTION, forget=True)

    def _main_module_timeout_handler(self):
        self.test_host.terminate()
        self._module_callback(exception=self._TIMEOUT_EXCEPTION)

    def _external_dhcp_timeout_handler(self):
        # Attempt to scan for this device
        def callback(device_ip):
            if device_ip:
                if self.state != _STATE.WAITING:
                    self.logger.warn('Dropping dhcp callback %s in state %s',
                                     self.target_mac, self.state)
                    return
                self.runner.ip_notify(MODE.NOPE, {
                    'type': 'STATIC',
                    'mac': self.target_mac,
                    'ip': str(device_ip),
                    'delta': -1
                }, self.gateway)
            else:
                self._aux_module_timeout_handler()
        self.logger.warn('Monitoring timeout for external dhcp. '
                         'Attempting to scan for device %s', self.target_mac)
        external_subnets = [ip_network(subnet['subnet']) for subnet in self.runner.config.get(
            'external_subnets', [])]
        self.gateway.discover_host(self.target_mac, external_subnets, callback)

    def heartbeat(self):
        """Checks module run time for each event loop"""
        timeout_sec = self._get_test_timeout(self.test_name)
        if self.test_host:
            self.test_host.heartbeat()
        if not timeout_sec or not self.test_start or self._no_test:
            return
        timeout = gcp.parse_timestamp(self.test_start) + timedelta(seconds=timeout_sec)
        nowtime = gcp.parse_timestamp(gcp.get_timestamp())
        if nowtime >= timeout:
            if self.timeout_handler:
                self.logger.error('Monitoring timeout for %s after %ds', self.test_name,
                                  timeout_sec)
                # ensure it's called once
                handler, self.timeout_handler = self.timeout_handler, None
                handler()

    def register_dhcp_ready_listener(self, callback):
        """Registers callback for when the host is ready for activation"""
        assert callable(callback), "ip listener callback is not callable"
        self._dhcp_listeners.append(callback)

    def _finalize_report(self):
        report_paths, test_results = self._report.finalize()
        if self._trigger_path:
            report_paths.update({'trigger_path': self._trigger_path})
        self.logger.info('Finalized with reports %s', list(report_paths.keys()))
        report_blobs = {name: self._upload_file(path) for name, path in report_paths.items()}
        self.record_result('terminate', state=MODE.TERM, **report_blobs)
        self._report = None

        return test_results

    def terminate(self, reason, trigger=True):
        """Terminate this host"""
        self.logger.info('Target device %s terminate, running %s, trigger %s: %s', self,
                         self._host_name(), trigger, reason)
        self._state_transition(_STATE.TERM)
        self._release_config()
        self._monitor_cleanup()
        if self.target_port:
            self.runner.network.delete_mirror_interface(self.target_port)

        if self.test_host:
            try:
                self.test_host.terminate()
                self.test_host = None
                self.timeout_handler = None
            except Exception as e:
                self.logger.error('Target device %s terminating test: %s', self, self.test_name)
                self.logger.exception(e)
        if trigger:
            self.runner.target_set_complete(self.device,
                                            'Target device %s termination: %s' % (
                                                self, self.test_host))
        test_results = self._finalize_report()
        return test_results

    def idle_handler(self):
        """Trigger events from idle state"""
        if self.state == _STATE.INIT:
            self._prepare()
        elif self.state == _STATE.BASE:
            self._base_start()

    def ip_notify(self, target_ip, state=MODE.DONE, delta_sec=-1):
        """Handle completion of ip subtask"""
        self._trigger_path = os.path.join(self.scan_base, 'ip_triggers.txt')
        with open(self._trigger_path, 'a') as output_stream:
            output_stream.write('%s %s %d\n' % (target_ip, state, delta_sec))
        self._all_ips.append({"ip": target_ip, "timestamp": time.time()})
        # Update ip directly if it's already triggered.
        if self.target_ip:
            self.target_ip = target_ip
        if self.test_host:
            self.test_host.ip_listener(target_ip, state)

    def trigger_ready(self):
        """Check if this host is ready to be triggered"""
        if self.state != _STATE.WAITING:
            return False
        delta_t = datetime.now() - self._startup_time
        if delta_t < timedelta(seconds=self._STARTUP_MIN_TIME_SEC):
            return False
        if self._get_dhcp_mode() == DhcpMode.IP_CHANGE:
            return len(set(map(lambda ip: ip["ip"], self._all_ips))) > 1
        return True

    def trigger(self, state=MODE.DONE, target_ip=None, exception=None, delta_sec=-1):
        """Handle device trigger"""
        if not self.target_ip and not self.trigger_ready():
            self.logger.warning('Target device %s ignoring premature trigger', self)
            return False
        if self.target_ip:
            self.logger.debug('Target device %s already triggered', self)
            assert self.target_ip == target_ip, "target_ip mismatch"
            return True
        self.target_ip = target_ip
        self._record_result('info', state='%s/%s' % (self.target_mac, target_ip))
        self.record_result('acquire', ip=target_ip, state=state, exception=exception)
        if exception:
            self._state_transition(_STATE.ERROR)
            self.runner.target_set_error(self.device, exception)
        else:
            self.logger.info('Target device %s triggered as %s', self, target_ip)
            self._state_transition(_STATE.BASE, _STATE.WAITING)
        return True

    def _ping_test(self, src, dst, src_addr=None):
        if not src or not dst:
            self.logger.error('Invalid ping test params, src=%s, dst=%s', src, dst)
            return False
        return self.runner.ping_test(src, dst, src_addr=src_addr)

    def _startup_scan(self):
        self._startup_file = os.path.join(self.scan_base, 'startup.pcap')
        self._startup_time = datetime.now()
        self.logger.info('Target device %s startup pcap capture', self)
        self._monitor_scan(self._startup_file)

    def _shorten_filename(self, long_name):
        if long_name and long_name.startswith(self._PATH_PREFIX):
            return long_name[len(self._PATH_PREFIX) + 1:]
        return long_name

    def _monitor_scan(self, output_file, timeout=None):
        assert not self._monitor_ref, 'tcp_monitor already active'
        network = self.runner.network
        tcp_filter = ''
        self.logger.info('Target device %s pcap intf %s for %s seconds output in %s',
                         self, self._mirror_intf_name, timeout if timeout else 'infinite',
                         self._shorten_filename(output_file))
        helper = tcpdump_helper.TcpdumpHelper(network.pri, tcp_filter, packets=None,
                                              intf_name=self._mirror_intf_name,
                                              timeout=timeout, pcap_out=output_file,
                                              blocking=False)
        self._monitor_ref = helper
        self._monitor_start = datetime.now()
        self.runner.monitor_stream('tcpdump', self._monitor_ref.stream(),
                                   self._monitor_ref.next_line, error=self._monitor_error,
                                   hangup=functools.partial(self._monitor_timeout, timeout))

    def _base_start(self):
        try:
            success = self._base_tests()
            self._monitor_cleanup()
            if not success:
                self.logger.warning('Target device %s base tests failed', self)
                self._state_transition(_STATE.ERROR)
                return
            self.logger.info('Target device %s done with base.', self)
            self._background_scan()
        except Exception as e:
            self._monitor_cleanup()
            self._monitor_error(e)

    def _monitor_cleanup(self, forget=True):
        if self._monitor_ref:
            self.logger.info('Target device %s network pcap complete', self)
            active = self._monitor_ref.stream() and not self._monitor_ref.stream().closed
            assert active == forget, 'forget and active mismatch'
            self._upload_file(self._startup_file)
            if forget:
                self.runner.monitor_forget(self._monitor_ref.stream())
                self._monitor_ref.terminate()
            self._monitor_ref = None

    def _monitor_error(self, exception, forget=False):
        self.logger.error('Target device %s monitor error: %s', self, exception)
        self._monitor_cleanup(forget=forget)
        self.record_result(self.test_name, exception=exception)
        self._state_transition(_STATE.ERROR)
        self.runner.target_set_error(self.device, exception)

    def _background_scan(self):
        self._state_transition(_STATE.MONITOR, _STATE.BASE)
        if not self._monitor_scan_sec:
            self.logger.info('Target device %s skipping background pcap', self)
            self._monitor_continue()
            return
        self.record_result('monitor', time=self._monitor_scan_sec, state=MODE.EXEC)
        monitor_file = os.path.join(self.scan_base, 'monitor.pcap')
        self.logger.info('Target device %s background pcap for %ds',
                         self, self._monitor_scan_sec)
        self._monitor_scan(monitor_file, timeout=self._monitor_scan_sec)

    def _monitor_timeout(self, timeout):
        duration = datetime.now() - self._monitor_start
        if not timeout or duration < timedelta(seconds=timeout):
            self._monitor_error(Exception('tcpdump pcap hangup'))
            return
        self._monitor_complete()

    def _monitor_complete(self):
        self.logger.info('Target device %s pcap complete', self)
        self._monitor_cleanup(forget=False)
        self.record_result('monitor', state=MODE.DONE)
        self._monitor_continue()

    def _monitor_continue(self):
        self._state_transition(_STATE.NEXT, _STATE.MONITOR)
        self.test_name = None
        self._run_next_test()

    def _base_tests(self):
        self.record_result('base', state=MODE.EXEC)
        if not self._ping_test(self.gateway.host, self.target_ip):
            self.logger.debug('Target device %s warmup ping failed', self)
        try:
            success1 = self._ping_test(self.gateway.host, self.target_ip), 'simple ping failed'
            success2 = self._ping_test(self.gateway.host, self.target_ip,
                                       src_addr=self.fake_target), 'target ping failed'
            if not success1 or not success2:
                return False
        except Exception as e:
            self.record_result('base', exception=e)
            self._monitor_cleanup()
            raise
        self.record_result('base', state=MODE.DONE)
        return True

    def _run_next_test(self):
        assert not self.test_name, 'test_name defined: %s' % self.test_name
        try:
            if self.remaining_tests:
                self.logger.debug('Target device %s executing tests %s',
                                  self, self.remaining_tests)
                self._run_test(self.remaining_tests.pop(0))
            elif self._no_test:
                self.logger.info('Target device %s entering no test hold', self)
                self._state_transition(_STATE.HOLD, _STATE.NEXT)
            else:
                self.logger.info('Target device %s no more tests remaining', self)
                self.timeout_handler = self._aux_module_timeout_handler
                self._state_transition(_STATE.DONE, _STATE.NEXT)
                self.record_result('finish', state=MODE.FINE)
        except Exception as e:
            self.logger.error('Target device %s start error: %s', self, e)
            self._state_transition(_STATE.ERROR)
            self.runner.target_set_error(self.device, e)

    def _inst_config_path(self):
        return os.path.abspath(os.path.join(self._INST_DIR, self._CONFIG_DIR))

    def _device_aux_path(self):
        path = os.path.join(self._device_base, self._AUX_DIR)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def _new_test(self, test_name):
        if test_name in self.config['test_metadata']:
            metadatum = self.config['test_metadata'][test_name]
            startup_cmd = metadatum['startup_cmd']
            basedir = os.path.abspath(metadatum['basedir'])
            new_root = os.path.abspath(os.path.join(self.devdir, 'test_root'))
            if os.path.isdir(new_root):
                shutil.rmtree(new_root)
            os.makedirs(new_root)
            for src_file in os.listdir(basedir):
                src_full = os.path.join(basedir, src_file)
                os.symlink(src_full, os.path.join(new_root, src_file))
            return NativeModule(self, self.devdir, test_name, self._loaded_config, new_root,
                                startup_cmd)
        clazz = IpAddrModule if test_name == 'ipaddr' else DockerModule
        return clazz(self, self.devdir, test_name, self._loaded_config)

    def _run_test(self, test_name):
        self.timeout_handler = self._main_module_timeout_handler
        self.test_host = self._new_test(test_name)

        self.logger.info('Target device %s start %s', self, self._host_name())

        try:
            self.test_port = self.gateway.allocate_test_port()
        except Exception as e:
            self.test_host = None
            raise e

        try:
            self._start_test(test_name)
            params = self._get_module_params()
            self.test_host.start(self.test_port, params, self._module_callback, self._finish_hook)
        except Exception as e:
            self.test_host = None
            self.gateway.release_test_port(self.test_port)
            self.test_port = None
            self._monitor_cleanup()
            raise e

    def _start_test(self, test_name):
        self.test_name = test_name
        self.test_start = gcp.get_timestamp()
        self._write_module_config(self._loaded_config, self._host_tmp_path())
        self._record_result(self.test_name, config=self._loaded_config, state=MODE.CONF)
        self.record_result(self.test_name, state=MODE.EXEC)
        self._monitor_scan(os.path.join(self.scan_base, 'test_%s.pcap' % self.test_name))
        self._state_transition(_STATE.TESTING, _STATE.NEXT)

    def _end_test(self, state=MODE.DONE, return_code=None, exception=None):
        self._monitor_cleanup()
        self._state_transition(_STATE.NEXT, _STATE.TESTING)
        report_path = os.path.join(self._host_tmp_path(), 'report.txt')
        activation_log_path = os.path.join(self._host_dir_path(), 'activate.log')
        module_config_path = os.path.join(self._host_tmp_path(), self._MODULE_CONFIG)
        remote_paths = {}
        for result_type, path in ((ResultType.REPORT_PATH, report_path),
                                  (ResultType.ACTIVATION_LOG_PATH, activation_log_path),
                                  (ResultType.MODULE_CONFIG_PATH, module_config_path)):
            if os.path.isfile(path):
                self._report.accumulate(self.test_name, {result_type: path})
                remote_paths[result_type.value] = self._upload_file(path)
        self.record_result(self.test_name, state=state, code=return_code, exception=exception,
                           **remote_paths)
        self.test_name = None
        self.test_host = None
        self.timeout_handler = None
        self._run_next_test()

    def _get_module_params(self):
        switch_setup = self.switch_setup if 'mods_addr' in self.switch_setup else None
        ext_loip = switch_setup.get('mods_addr') % self.test_port if switch_setup else None
        params = {
            'local_ip': ext_loip,
            'target_ip': self.target_ip,
            'target_mac': self.target_mac,
            'target_port': str(self.target_port) if self.target_port else None,
            'gateway_ip': self.gateway.host.IP(),
            'gateway_mac': self.gateway.host.MAC(),
            'inst_base': self._inst_config_path(),
            'port_base': self._port_base,
            'device_base': self._device_aux_path(),
            'type_base': self._type_aux_path(),
            'gw_base': self.gateway.get_base_dir(),
            'scan_base': self.scan_base
        }
        if ext_loip:
            params.update(self._get_switch_config())
        return params

    def _get_switch_config(self):
        return {
            'ip': self.switch_setup.get('ip_addr'),
            'model': self.switch_setup.get('model'),
            'username': self.switch_setup.get('username'),
            'password': self.switch_setup.get('password')
        }

    def _host_name(self):
        return self.test_host.host_name if self.test_host else 'unknown'

    def _host_dir_path(self):
        return os.path.join(self.devdir, 'nodes', self._host_name())

    def _host_tmp_path(self):
        return os.path.join(self._host_dir_path(), 'tmp')

    def _finish_hook(self):
        script = self.config.get('finish_hook')
        if script:
            finish_dir = os.path.join(self.devdir, 'finish', self._host_name())
            shutil.rmtree(finish_dir, ignore_errors=True)
            os.makedirs(finish_dir)
            self.logger.info('Executing finish_hook: %s %s', script, finish_dir)
            os.system('%s %s 2>&1 > %s/finish.out' % (script, finish_dir, finish_dir))

    def _topology_hook(self):
        if self._topology_hook_script:
            update_dir = self._NETWORK_DIR
            self.logger.info('Executing topology_hook: %s %s',
                             self._topology_hook_script, update_dir)
            os.system('%s %s 2>&1 > %s/update.out' %
                      (self._topology_hook_script, update_dir, update_dir))

    def _module_callback(self, return_code=None, exception=None):
        host_name = self._host_name()
        self.logger.info('Host callback %s/%s was %s with %s',
                         self.test_name, host_name, return_code, exception)
        failed = return_code or exception
        state = MODE.MERR if failed else MODE.DONE
        self.gateway.release_test_port(self.test_port)
        assert self.test_host, '_module_callback with no test_host defined'
        self._end_test(state=state, return_code=return_code, exception=exception)

    def _merge_run_info(self, config):
        config['run_info'] = {
            'run_id': self.run_id,
            'mac_addr': self.target_mac,
            'started': gcp.get_timestamp(),
            'switch': self._get_switch_config(),
            'usi': self._usi_config
        }
        config['run_info'].update(self.runner.get_run_info())

    def _load_module_config(self, run_info=True):
        config = self.runner.get_base_config()
        if run_info:
            self._merge_run_info(config)
        self._load_config('type', config, self._type_path(), self._TYPE_CONFIG)
        self._load_config('device', config, self._device_base, self._DEVICE_CONFIG)
        self._load_config('port', config, self._port_base, self._PORT_CONFIG)
        return config

    def record_result(self, name, **kwargs):
        """Record a named result for this test"""
        current = gcp.get_timestamp()
        if name != self.test_name:
            self.logger.debug('Target device %s report %s start %s',
                              self, name, current)
            self.test_name = name
            self.test_start = current
        if name:
            self._record_result(name, current, **kwargs)
            if kwargs.get("exception"):
                self._report.accumulate(name, {ResultType.EXCEPTION: str(kwargs["exception"])})
            if "code" in kwargs:
                self._report.accumulate(name, {ResultType.RETURN_CODE: kwargs["code"]})
            self._report.accumulate(name, {ResultType.MODULE_CONFIG: self._loaded_config})

    def _record_result(self, name, run_info=True, current=None, **kwargs):
        result = {
            'name': name,
            'runid': (self.run_id if run_info else None),
            'daq_run_id': self.runner.daq_run_id,
            'device_id': self.target_mac,
            'started': self.test_start,
            'timestamp': current if current else gcp.get_timestamp(),
            'port': (self.target_port if run_info else None)
        }
        result.update(kwargs)
        if 'exception' in result:
            result['exception'] = self._exception_message(result['exception'])
        if name:
            self.results[name] = result
        self._gcp.publish_message('daq_runner', 'test_result', result)
        return result

    def _exception_message(self, exception):
        if not exception or exception == 'None':
            return None
        if isinstance(exception, Exception):
            return exception.__class__.__name__
        return str(exception)

    def _control_updated(self, control_config):
        self.logger.info('Updated control config: %s %s', self, control_config)
        paused = control_config.get('paused')
        if not paused and self.is_ready():
            self._start_run()
        elif paused and not self.is_ready():
            self.logger.warning('Inconsistent control state for update of %s', self)

    def reload_config(self):
        """Trigger a config reload due to an external config change."""
        device_ready = self.is_ready()
        new_config = self._load_module_config(run_info=device_ready)
        if device_ready:
            self._loaded_config = new_config
        config_bundle = self._make_config_bundle(new_config)
        self.logger.info('Device config reloaded: %s %s', device_ready, self)
        self._record_result(None, run_info=device_ready, config=config_bundle)
        return new_config

    def _dev_config_updated(self, dev_config):
        self.logger.info('Device config update: %s %s', self, dev_config)
        self._write_module_config(dev_config, self._device_base)
        self.reload_config()

    def _initialize_config(self):
        dev_config = self._load_config('base', {}, self._device_base, self._BASE_CONFIG)
        self._gcp.register_config(self._DEVICE_PATH % self.target_mac,
                                  dev_config, self._dev_config_updated)
        if self.target_port:
            self._gcp.register_config(self._CONTROL_PATH % self.target_port,
                                      self._make_control_bundle(),
                                      self._control_updated, immediate=True)
        self._record_result(None, config=self._make_config_bundle())

    def _release_config(self):
        self._gcp.release_config(self._DEVICE_PATH % self.target_mac)
        if self.target_port:
            self._gcp.release_config(self._CONTROL_PATH % self.target_port)

    def __repr__(self):
        return str(self.device) + (" on port %d" % self.target_port if self.target_port else "")
