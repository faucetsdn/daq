"""Main test runner for DAQ"""

import copy
import os
import re
import threading
import time
import traceback
import uuid
from datetime import datetime, timedelta, timezone

import configurator
import faucet_event_client
import gateway as gateway_manager
import gcp
import host as connected_host
import network
import stream_monitor
from wrappers import DaqException
import logger

LOGGER = logger.get_logger('runner')


class PortInfo:
    """Simple container for device port info"""
    active = False
    flapping_start = None
    port_no = None


class IpInfo:
    """Simple container for device ip info"""
    ip_addr = None
    state = None
    delta_sec = None


class Device:
    """Simple container for device info"""
    def __init__(self):
        self.mac = None
        self.host = None
        self.gateway = None
        self.group = None
        self.port = None
        self.dhcp_ready = False
        self.ip_info = IpInfo()
        self.set_id = None

    def __repr__(self):
        return self.mac.replace(":", "")


class Devices:
    """Container for all devices"""
    def __init__(self):
        self._devices = {}
        self._set_ids = set()

    def new_device(self, mac, port_info=None):
        """Adding a new device"""
        assert mac not in self._devices, "Device with mac: %s is already added." % mac
        device = Device()
        device.mac = mac
        self._devices[mac] = device
        device.port = port_info if port_info else PortInfo()
        port_no = device.port.port_no
        set_id = port_no if port_no else self._allocate_set_id()
        assert set_id not in self._set_ids, "Duplicate device set id %d" % set_id
        self._set_ids.add(set_id)
        device.set_id = set_id
        return device

    def _allocate_set_id(self):
        set_id = 1
        while set_id in self._set_ids:
            set_id += 1
        return set_id

    def remove(self, device):
        """Removing a device"""
        assert self.contains(device), "Device %s not found." % device
        del self._devices[device.mac]
        self._set_ids.remove(device.set_id)

    def get(self, device_mac):
        """Get a device using its mac address"""
        return self._devices.get(device_mac)

    def get_by_port_info(self, port):
        """Get a device using its port info object"""
        for device in self._devices.values():
            if device.port == port:
                return device
        return None

    def get_by_gateway(self, gateway):
        """Get devices under specified gateway"""
        return [device for device in self._devices.values() if device.gateway == gateway]

    def get_by_group(self, group_name):
        """Get devices under a group name"""
        return [device for device in self._devices.values() if device.group == group_name]

    def get_all_devices(self):
        """Get all devices"""
        return list(self._devices.values())

    def get_triggered_devices(self):
        """Get devices with hosts"""
        return [device for device in self._devices.values() if device.host]

    def contains(self, device):
        """Returns true if the device is expected"""
        return self._devices.get(device.mac) == device

class DAQRunner:
    """Main runner class controlling DAQ. Primarily mediates between
    faucet events, connected hosts (to test), and gcp for logging. This
    class owns the main event loop and shards out work to subclasses."""

    MAX_GATEWAYS = 9
    _DEFAULT_RETENTION_DAYS = 30
    _MODULE_CONFIG = 'module_config.json'
    _RUNNER_CONFIG_PATH = 'runner/setup'
    _DEFAULT_TESTS_FILE = 'config/modules/host.conf'
    _RESULT_LOG_FILE = 'inst/result.log'

    def __init__(self, config):
        self.configurator = configurator.Configurator()
        self.gateway_sets = set(range(1, self.MAX_GATEWAYS+1))
        self.config = config
        self._result_sets = {}
        self._devices = Devices()
        self._ports = {}
        self._callback_queue = []
        self._callback_lock = threading.Lock()
        self.gcp = gcp.GcpManager(self.config, self._queue_callback)
        self._base_config = self._load_base_config()
        self.description = config.get('site_description', '').strip('\"')
        self._daq_version = os.environ['DAQ_VERSION']
        self._lsb_release = os.environ['DAQ_LSB_RELEASE']
        self._sys_uname = os.environ['DAQ_SYS_UNAME']
        self.network = network.TestNetwork(config)
        self.result_linger = config.get('result_linger', False)
        self._linger_exit = 0
        self.faucet_events = None
        self.single_shot = config.get('single_shot', False)
        self.fail_mode = config.get('fail_mode', False)
        self.run_trigger_type = config.get('run_trigger_type', 'PORT')
        self.run_tests = True
        self.stream_monitor = None
        self.exception = None
        self.run_count = 0
        self.run_limit = int(config.get('run_limit', 0))
        self._default_port_flap_timeout = int(config.get('port_flap_timeout_sec', 0))
        self.result_log = self._open_result_log()
        self._system_active = False
        logging_client = self.gcp.get_logging_client()
        self.daq_run_id = self._init_daq_run_id()
        if logging_client:
            logger.set_stackdriver_client(logging_client,
                                          labels={"daq_run_id": self.daq_run_id})
        test_list = self._get_test_list(config.get('host_tests', self._DEFAULT_TESTS_FILE), [])
        if self.config.get('keep_hold'):
            LOGGER.info('Appending test_hold to master test list')
            test_list.append('hold')
        config['test_list'] = test_list
        LOGGER.info('DAQ RUN id: %s' % self.daq_run_id)
        LOGGER.info('Configured with tests %s' % ', '.join(config['test_list']))
        LOGGER.info('DAQ version %s' % self._daq_version)
        LOGGER.info('LSB release %s' % self._lsb_release)
        LOGGER.info('system uname %s' % self._sys_uname)

    def _open_result_log(self):
        return open(self._RESULT_LOG_FILE, 'w')

    def _get_states(self):
        states = connected_host.pre_states() + self.config['test_list']
        return states + connected_host.post_states()

    def _init_daq_run_id(self):
        daq_run_id = str(uuid.uuid4())
        with open('inst/daq_run_id.txt', 'w') as output_stream:
            output_stream.write(daq_run_id + '\n')
        return daq_run_id

    def _send_heartbeat(self):
        message = {
            'name': 'status',
            'states': self._get_states(),
            'ports': self._get_active_ports(),
            'description': self.description,
            'timestamp': time.time()
        }
        message.update(self.get_run_info())
        self.gcp.publish_message('daq_runner', 'heartbeat', message)

    def get_run_info(self):
        """Return basic run info dict"""
        info = {
            'version': self._daq_version,
            'lsb': self._lsb_release,
            'uname': self._sys_uname,
            'daq_run_id': self.daq_run_id
        }
        data_retention_days = self.config.get('run_data_retention_days',
                                              self._DEFAULT_RETENTION_DAYS)
        if data_retention_days:
            expiration = datetime.now(timezone.utc) + timedelta(days=float(data_retention_days))
            info['expiration'] = gcp.to_timestamp(expiration)
        return info

    def initialize(self):
        """Initialize DAQ instance"""
        self._send_heartbeat()
        self._publish_runner_config(self._base_config)

        self.network.initialize()

        LOGGER.debug('Attaching event channel...')
        self.faucet_events = faucet_event_client.FaucetEventClient(self.config)
        self.faucet_events.connect()

        LOGGER.info('Waiting for system to settle...')
        time.sleep(3)

        LOGGER.debug('Done with initialization')

    def cleanup(self):
        """Cleanup instance"""
        try:
            LOGGER.info('Stopping network...')
            self.network.stop()
        except Exception as e:
            LOGGER.error('Cleanup exception: %s', e)
        if self.result_log:
            self.result_log.close()
            self.result_log = None
        LOGGER.info('Done with runner.')

    def add_host(self, *args, **kwargs):
        """Add a host with the given parameters"""
        return self.network.add_host(*args, **kwargs)

    def remove_host(self, host):
        """Remove the given host"""
        return self.network.remove_host(host)

    def get_host_interface(self, host):
        """Get the internal interface for the host"""
        return self.network.get_host_interface(host)

    def _handle_faucet_events(self):
        while self.faucet_events:
            event = self.faucet_events.next_event()
            if not event:
                break
            (dpid, port, active) = self.faucet_events.as_port_state(event)
            if dpid and port:
                LOGGER.debug('port_state: %s %s', dpid, port)
                self._handle_port_state(dpid, port, active)
                return
            (dpid, port, target_mac, vid) = self.faucet_events.as_port_learn(event)
            if dpid and port and vid:
                if self.run_trigger_type == "PORT":
                    self._handle_port_learn(dpid, port, vid, target_mac)
                elif self.run_trigger_type == "VLAN" and self.network.is_system_port(dpid, port):
                    self._handle_device_learn(vid, target_mac)
                return
            (dpid, restart_type) = self.faucet_events.as_config_change(event)
            if dpid is not None:
                LOGGER.debug('dp_id %d restart %s', dpid, restart_type)

    def _handle_port_state(self, dpid, port, active):
        if self.network.is_system_port(dpid, port):
            LOGGER.info('System port %s on dpid %s is active %s', port, dpid, active)
            if self._system_active and not active:
                LOGGER.error('System port became inactive, terminating.')
                self.exception = DaqException('System port inactive')
                self.shutdown()
            self._system_active = active
            return
        if not self.network.is_device_port(dpid, port):
            LOGGER.debug('Unknown port %s on dpid %s is active %s', port, dpid, active)
            return

        if port not in self._ports:
            self._ports[port] = PortInfo()
            self._ports[port].port_no = port

        if active != self._ports[port].active:
            LOGGER.info('Port %s dpid %s is now %s', port, dpid, "active" if active else "inactive")
        if active:
            self._activate_port(port)
        else:
            device = self._devices.get_by_port_info(self._ports[port])
            port_info = self._ports[port]
            if device and device.host and not port_info.flapping_start:
                port_info.flapping_start = time.time()
            if port_info.active:
                if device and not port_info.flapping_start:
                    self._direct_port_traffic(device.mac, port, None)
                self._deactivate_port(port)
        self._send_heartbeat()

    def _activate_port(self, port):
        port_info = self._ports[port]
        port_info.flapping_start = 0
        port_info.active = True

    def _deactivate_port(self, port):
        port_info = self._ports[port]
        port_info.active = False

    def _direct_port_traffic(self, mac, port, target):
        self.network.direct_port_traffic(mac, port, target)

    def _handle_port_learn(self, dpid, port, vid, target_mac):
        if self.network.is_device_port(dpid, port):
            LOGGER.info('Port %s dpid %s learned %s', port, dpid, target_mac)
            if port not in self._ports:
                self._ports[port] = PortInfo()
                self._ports[port].port_no = port
            if not self._devices.get(target_mac):
                self._devices.new_device(target_mac, port_info=self._ports[port])
            self._target_set_trigger(self._devices.get(target_mac))
        else:
            LOGGER.debug('Port %s dpid %s learned %s (ignored)', port, dpid, target_mac)

    def _handle_device_learn(self, vid, target_mac):
        LOGGER.info('%s learned on vid %s', target_mac, vid)
        if not self._devices.get(target_mac):
            device = self._devices.new_device(target_mac)
        else:
            device = self._devices.get(target_mac)
        self._target_set_trigger(device)

    def _queue_callback(self, callback):
        with self._callback_lock:
            LOGGER.debug('Register callback')
            self._callback_queue.append(callback)

    def _handle_queued_events(self):
        with self._callback_lock:
            callbacks = self._callback_queue
            self._callback_queue = []
            if callbacks:
                LOGGER.debug('Processing %d callbacks', len(callbacks))
            for callback in callbacks:
                callback()

    def _handle_system_idle(self):
        # Some synthetic faucet events don't come in on the socket, so process them here.
        self._handle_faucet_events()
        all_idle = True
        for device in self._devices.get_triggered_devices():
            try:
                if device.host.is_running():
                    all_idle = False
                    device.host.idle_handler()
                else:
                    self.target_set_complete(device, 'target set not active')
            except Exception as e:
                self.target_set_error(device, e)
        for device in self._devices.get_all_devices():
            self._target_set_trigger(device)
            all_idle = False
        if not self._devices.get_triggered_devices() and not self.run_tests:
            if self.faucet_events and not self._linger_exit:
                self.shutdown()
            if self._linger_exit == 1:
                self._linger_exit = 2
                LOGGER.warning('Result linger on exit.')
            all_idle = False
        if all_idle:
            LOGGER.debug('No active device, waiting for trigger event...')

    def _reap_stale_ports(self):
        for device in self._devices.get_triggered_devices():
            if not device.port.flapping_start:
                continue
            timeout_sec = device.host.get_port_flap_timeout(device.host.test_name)
            if timeout_sec is None:
                timeout_sec = self._default_port_flap_timeout
            if (device.port.flapping_start + timeout_sec) <= time.time():
                exception = DaqException('port not active for %ds' % timeout_sec)
                self.target_set_error(device, exception)
                device.port.flapping_start = 0

    def shutdown(self):
        """Shutdown this runner by closing all active components"""
        self._terminate()
        self.monitor_forget(self.faucet_events.sock)
        self.faucet_events.disconnect()
        self.faucet_events = None
        count = self.stream_monitor.log_monitors(as_info=True)
        LOGGER.warning('No active ports remaining (%d monitors), ending test run.', count)
        self._send_heartbeat()

    def _loop_hook(self):
        self._handle_queued_events()
        states = {device.mac: device.host.state for device in self._devices.get_triggered_devices()}
        LOGGER.debug('Active target sets/state: %s', states)

    def _terminate(self):
        for device in self._devices.get_triggered_devices():
            self.target_set_error(device, DaqException('terminated'))

    def _module_heartbeat(self):
        # Should probably be converted to a separate thread to timeout any blocking fn calls
        _ = [device.host.heartbeat() for device in self._devices.get_triggered_devices()]

    def main_loop(self):
        """Run main loop to execute tests"""

        try:
            monitor = stream_monitor.StreamMonitor(idle_handler=self._handle_system_idle,
                                                   loop_hook=self._loop_hook,
                                                   timeout_sec=20)  # Polling rate
            self.stream_monitor = monitor
            self.monitor_stream('faucet', self.faucet_events.sock, self._handle_faucet_events,
                                priority=10)
            LOGGER.info('Entering main event loop.')
            LOGGER.info('See docs/troubleshooting.md if this blocks for more than a few minutes.')
            while self.stream_monitor.event_loop():
                self._reap_stale_ports()
                self._module_heartbeat()
        except Exception as e:
            LOGGER.error('Event loop exception: %s', e)
            LOGGER.exception(e)
            self.exception = e
        except KeyboardInterrupt as e:
            LOGGER.error('Keyboard Interrupt')
            LOGGER.exception(e)
            self.exception = e

        if self.config.get('use_console'):
            LOGGER.info('Dropping into interactive command line')
            self.network.cli()

        self._terminate()

    def _target_set_trigger(self, device):
        assert self._devices.contains(device), 'Target device %s is not expected' % device.mac
        port_trigger = device.port.port_no is not None
        if port_trigger:
            assert device.port.active, 'Target port %d is not active' % device.port.port_no

        if not self._system_active:
            LOGGER.warning('Target device %s ignored, system is not active', device.mac)
            return False

        if device.host:
            LOGGER.debug('Target device %s already triggered', device.mac)
            return False

        if not self.run_tests:
            LOGGER.debug('Target device %s trigger suppressed', device.mac)
            return False

        try:
            group_name = self.network.device_group_for(device.mac)
            device.group = group_name
            gateway = self._activate_device_group(device)
            if gateway.activated:
                LOGGER.debug('Target device %s trigger ignored b/c activated gateway', device.mac)
                return False
        except Exception as e:
            LOGGER.error('Target device %s target trigger error %s', device.mac, str(e))
            if self.fail_mode:
                LOGGER.warning('Suppressing further tests due to failure.')
                self.run_tests = False
            return False

        # Stops all DHCP response initially
        # Selectively enables dhcp response at ipaddr stage based on dhcp mode
        gateway.stop_dhcp_response(device.mac)
        gateway.attach_target(device)
        device.gateway = gateway
        try:
            self.run_count += 1
            new_host = connected_host.ConnectedHost(self, device, self.config)
            device.host = new_host
            new_host.register_dhcp_ready_listener(self._dhcp_ready_listener)
            new_host.initialize()

            if port_trigger:
                target = {
                    'port': device.port.port_no,
                    'group': group_name,
                    'fake': gateway.fake_target,
                    'port_set': gateway.port_set,
                    'mac': device.mac
                }
                self._direct_port_traffic(device.mac, device.port.port_no, target)
            return True
        except Exception as e:
            self.target_set_error(device, e)

    def _get_test_list(self, test_file, test_list):
        no_test = self.config.get('no_test', False)
        if no_test:
            LOGGER.warning('Suppressing configured tests because no_test')
            return test_list
        LOGGER.info('Reading test definition file %s', test_file)
        with open(test_file) as file:
            line = file.readline()
            while line:
                cmd = re.sub(r'#.*', '', line).strip().split()
                cmd_name = cmd[0] if cmd else None
                argument = cmd[1] if len(cmd) > 1 else None
                if cmd_name == 'add':
                    LOGGER.debug('Adding test %s from %s', argument, test_file)
                    test_list.append(argument)
                elif cmd_name == 'remove':
                    if argument in test_list:
                        LOGGER.debug('Removing test %s from %s', argument, test_file)
                        test_list.remove(argument)
                elif cmd_name == 'include':
                    self._get_test_list(argument, test_list)
                elif cmd_name == 'build' or not cmd_name:
                    pass
                else:
                    LOGGER.warning('Unknown test list command %s', cmd_name)
                line = file.readline()
        return test_list

    def _activate_device_group(self, device):
        group_name = device.group
        group_devices = self._devices.get_by_group(group_name)
        existing_gateways = {device.gateway for device in group_devices if device.gateway}
        if existing_gateways:
            existing = existing_gateways.pop()
            LOGGER.info('Gateway for existing device group %s is %s', group_name, existing)
            return existing

        set_num = self._find_gateway_set(device)
        LOGGER.info('Gateway for device group %s not found, initializing base %d...',
                    device.group, set_num)
        gateway = gateway_manager.Gateway(self, group_name, set_num, self.network)
        try:
            gateway.initialize()
        except Exception:
            LOGGER.error('Cleaning up from failed gateway initialization')
            LOGGER.debug('Clearing %s gateway group %s for %s',
                         device, set_num, group_name)
            self.gateway_sets.add(set_num)
            raise
        return gateway

    def ip_notify(self, state, target, gateway, exception=None):
        """Handle a DHCP / Static IP notification"""
        if exception:
            assert not target, 'unexpected exception with target'
            LOGGER.error('IP exception for %s: %s', gateway, exception)
            LOGGER.exception(exception)
            self._terminate_gateway_set(gateway)
            return

        target_mac, target_ip, delta_sec = target['mac'], target['ip'], target['delta']
        LOGGER.info('IP notify %s is %s on %s (%s/%d)', target_mac,
                    target_ip, gateway, state, delta_sec)

        if not target_mac:
            LOGGER.warning('IP target mac missing')
            return

        device = self._devices.get(target_mac)
        device.ip_info.ip_addr = target_ip
        device.ip_info.state = state
        device.ip_info.delta_sec = delta_sec
        if device and device.host:
            device.host.ip_notify(target_ip, state, delta_sec)
            self._check_and_activate_gateway(device)

    def _get_active_ports(self):
        return [p.port_no for p in self._ports.values() if p.active]

    def _check_and_activate_gateway(self, device):
        # Host ready to be activated and DHCP happened / Static IP
        ip_info = device.ip_info
        if not ip_info.ip_addr or not device.dhcp_ready:
            return
        (gateway, ready_devices) = self._should_activate_target(device)

        if not ready_devices:
            return
        if ready_devices is True:
            device.host.trigger(ip_info.state, target_ip=ip_info.ip_addr,
                                delta_sec=ip_info.delta_sec)
        else:
            self._activate_gateway(ip_info.state, gateway, ready_devices, ip_info.delta_sec)

    def _dhcp_ready_listener(self, device):
        device.dhcp_ready = True
        self._check_and_activate_gateway(device)

    def _activate_gateway(self, state, gateway, ready_devices, delta_sec):
        gateway.activate()
        if len(ready_devices) > 1:
            state = 'group'
            delta_sec = -1
        for device in ready_devices:
            LOGGER.info('IP activating target %s', device)
            target_ip, delta_sec = device.ip_info.ip_addr, device.ip_info.delta_sec
            triggered = device.host.trigger(state, target_ip=target_ip, delta_sec=delta_sec)
            assert triggered, 'Device %s not triggered' % device

    def _should_activate_target(self, device):
        if not device.host:
            LOGGER.warning('DHCP targets missing %s', device)
            return False, False
        gateway, group_name = device.gateway, device.group
        if gateway.activated:
            LOGGER.info('DHCP activation group %s already activated', group_name)
            return gateway, True

        if not device.host.notify_activate():
            LOGGER.info('DHCP device %s ignoring spurious notify', device)
            return gateway, False

        ready_devices = gateway.target_ready(device)
        group_size = self.network.device_group_size(group_name)

        remaining = group_size - len(ready_devices)
        if remaining and self.run_tests:
            LOGGER.info('DHCP waiting for %d additional members of group %s', remaining, group_name)
            return gateway, False

        ready_trigger = all(map(lambda host: device.host.trigger_ready(), ready_devices))
        if not ready_trigger:
            LOGGER.info('DHCP device group %s not ready to trigger', group_name)
            return gateway, False

        return gateway, ready_devices

    def _terminate_gateway_set(self, gateway):
        gateway_devices = self._devices.get_by_gateway(gateway)
        assert gateway_devices, '%s not found' % gateway
        LOGGER.info('Terminating %s', gateway)
        for device in gateway_devices:
            self.target_set_error(device, DaqException('terminated'))

    def _find_gateway_set(self, device):
        if not self.gateway_sets:
            raise Exception('Could not allocate open gateway set')
        if device.port.port_no in self.gateway_sets:
            self.gateway_sets.remove(device.port.port_no)
            return device.port.port_no
        return self.gateway_sets.pop()

    @staticmethod
    def ping_test(src, dst, src_addr=None):
        """Test ping between hosts"""
        dst_name = dst if isinstance(dst, str) else dst.name
        dst_ip = dst if isinstance(dst, str) else dst.IP()
        from_msg = ' from %s' % src_addr if src_addr else ''
        LOGGER.info('Test ping %s->%s%s', src.name, dst_name, from_msg)
        failure = "ping FAILED"
        assert dst_ip != "0.0.0.0", "IP address not assigned, can't ping"
        ping_opt = '-I %s' % src_addr if src_addr else ''
        try:
            output = src.cmd('ping -c2', ping_opt, dst_ip, '> /dev/null 2>&1 || echo ', failure)
            return output.strip() != failure
        except Exception as e:
            LOGGER.info('Test ping failure: %s', e)
            return False

    def target_set_error(self, device, exception):
        """Handle an error in the target set"""
        running = bool(device.host)
        LOGGER.error('Target device %s running %s exception: %s', device, running, exception)
        LOGGER.exception(exception)
        if running:
            device.host.record_result(device.host.test_name, exception=exception)
            self.target_set_complete(device, str(exception))
        else:
            stack = ''.join(
                traceback.format_exception(etype=type(exception), value=exception,
                                           tb=exception.__traceback__))
            self._target_set_finalize(device,
                                      {'exception': {'exception': str(exception),
                                                     'traceback': stack}},
                                      str(exception))
            self._detach_gateway(device)

    def target_set_complete(self, device, reason):
        """Handle completion of a target_set"""
        self._target_set_finalize(device, device.host.results, reason)
        self._target_set_cancel(device)

    def _target_set_finalize(self, device, result_set, reason):
        results = self._combine_result_set(device, result_set)
        LOGGER.info('Target device %s finalize: %s (%s)', device, results, reason)
        if self.result_log:
            self.result_log.write('%s: %s\n' % (device, results))
            self.result_log.flush()

        suppress_tests = self.fail_mode or self.result_linger
        if results and suppress_tests:
            LOGGER.warning('Suppressing further tests due to failure.')
            self.run_tests = False
            if self.result_linger:
                self._linger_exit = 1
        self._result_sets[device] = result_set

    def _target_set_cancel(self, device):
        target_host = device.host
        if target_host:
            device.host = None
            target_gateway = device.gateway
            target_port = device.port.port_no
            LOGGER.info('Target device %s cancel (#%d/%s).', device.mac, self.run_count,
                        self.run_limit)

            results = self._combine_result_set(device, self._result_sets.get(device))
            this_result_linger = results and self.result_linger
            target_gateway_linger = target_gateway and target_gateway.result_linger
            if target_gateway_linger or this_result_linger:
                LOGGER.warning('Target device %s result_linger: %s', device.mac, results)
                if target_port:
                    self._activate_port(target_port)
                target_gateway.result_linger = True
            else:
                if target_port:
                    self._direct_port_traffic(device.mac, target_port, None)
                target_host.terminate('_target_set_cancel', trigger=False)
                if target_gateway:
                    self._detach_gateway(device)
            if self.run_limit and self.run_count >= self.run_limit and self.run_tests:
                LOGGER.warning('Suppressing future tests because run limit reached.')
                self.run_tests = False
            if self.single_shot and self.run_tests:
                LOGGER.warning('Suppressing future tests because test done in single shot.')
                self.run_tests = False
        self._devices.remove(device)
        LOGGER.info('Remaining target sets: %s', self._devices.get_triggered_devices())

    def _detach_gateway(self, device):
        target_gateway = device.gateway
        if not target_gateway:
            return
        device.gateway = None
        if not target_gateway.detach_target(device):
            LOGGER.info('Retiring %s. Last device: %s', target_gateway, device)
            self.gateway_sets.add(target_gateway.port_set)
            target_gateway.terminate()

    def monitor_stream(self, *args, **kwargs):
        """Monitor a stream"""
        return self.stream_monitor.monitor(*args, **kwargs)

    def monitor_forget(self, stream):
        """Forget monitoring a stream"""
        return self.stream_monitor.forget(stream)

    def _combine_results(self):
        results = []
        for result_set_key in self._result_sets:
            result_set = self._result_sets[result_set_key]
            results.extend(self._combine_result_set(result_set_key, result_set))
        return results

    def _combine_result_set(self, set_key, result_sets):
        results = []
        if not result_sets:
            return results
        result_set_keys = list(result_sets)
        result_set_keys.sort()
        for result_set_key in result_set_keys:
            result = result_sets[result_set_key]
            code_string = result['code'] if 'code' in result else None
            code = int(code_string) if code_string else 0
            name = result['name'] if 'name' in result else result_set_key
            exp_msg = result.get('exception')
            status = exp_msg if exp_msg else code if name != 'fail' else not code
            if status != 0:
                results.append('%s:%s:%s' % (set_key, name, status))
        return results

    def finalize(self):
        """Finalize this instance, returning error result code"""
        self.gcp.release_config(self._RUNNER_CONFIG_PATH)
        exception = self.exception
        failures = self._combine_results()
        if failures:
            LOGGER.error('Test failures: %s', failures)
        if exception:
            LOGGER.error('Exiting b/c of exception: %s', exception)
        if failures or exception:
            return 1
        return 0

    def _base_config_changed(self, new_config):
        LOGGER.info('Base config changed: %s', new_config)
        self.configurator.write_config(new_config, self.config.get('site_path'),
                                       self._MODULE_CONFIG)
        self._base_config = self._load_base_config(register=False)
        self._publish_runner_config(self._base_config)
        _ = [device.host.reload_config() for device in self._devices.get_triggered_devices()]

    def _load_base_config(self, register=True):
        base_conf = self.config.get('base_conf')
        LOGGER.info('Loading base module config from %s', base_conf)
        base = self.configurator.load_and_merge({}, base_conf)
        site_path = self.config.get('site_path')
        LOGGER.info('Loading site module config from %s', base_conf)
        site_config = self.configurator.load_config(site_path, self._MODULE_CONFIG, optional=True)
        if register:
            self.gcp.register_config(self._RUNNER_CONFIG_PATH, site_config,
                                     self._base_config_changed)
        return self.configurator.merge_config(base, site_config)

    def get_base_config(self):
        """Get the base configuration for this install"""
        return copy.deepcopy(self._base_config)

    def _publish_runner_config(self, loaded_config):
        result = {
            'timestamp': gcp.get_timestamp(),
            'config': loaded_config
        }
        self.gcp.publish_message('daq_runner', 'runner_config', result)
