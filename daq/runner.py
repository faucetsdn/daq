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
    flapping_start = 0
    mac = None
    host = None
    gateway = None


class DAQRunner:
    """Main runner class controlling DAQ. Primarily mediates between
    faucet events, connected hosts (to test), and gcp for logging. This
    class owns the main event loop and shards out work to subclasses."""

    MAX_GATEWAYS = 10
    _DEFAULT_RETENTION_DAYS = 30
    _MODULE_CONFIG = 'module_config.json'
    _RUNNER_CONFIG_PATH = 'runner/setup'
    _DEFAULT_TESTS_FILE = 'config/modules/host.conf'
    _RESULT_LOG_FILE = 'inst/result.log'

    def __init__(self, config):
        self.configurator = configurator.Configurator()
        self.config = config
        self._port_info = {}
        self._result_sets = {}
        self._mac_port_map = {}
        self._device_groups = {}
        self._gateway_sets = {}
        self._target_mac_ip = {}
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
        self.event_trigger = config.get('event_trigger', False)
        self.fail_mode = config.get('fail_mode', False)
        self.run_tests = True
        self.stream_monitor = None
        self.exception = None
        self.run_count = 0
        self.run_limit = int(config.get('run_limit', 0))
        self._default_port_flap_timeout = int(config.get('port_flap_timeout_sec', 0))
        self.result_log = self._open_result_log()
        self._system_active = False
        self._dhcp_ready = set()
        self._ip_info = {}
        logging_client = self.gcp.get_logging_client()
        self._daq_run_id = uuid.uuid4()
        if logging_client:
            logger.set_stackdriver_client(logging_client,
                                          labels={"daq_run_id": str(self._daq_run_id)})
        test_list = self._get_test_list(config.get('host_tests', self._DEFAULT_TESTS_FILE), [])
        if self.config.get('keep_hold'):
            LOGGER.info('Appending test_hold to master test list')
            test_list.append('hold')
        config['test_list'] = test_list
        LOGGER.info('DAQ RUN id: %s' % self._daq_run_id)
        LOGGER.info('Configured with tests %s' % ', '.join(config['test_list']))
        LOGGER.info('DAQ version %s' % self._daq_version)
        LOGGER.info('LSB release %s' % self._lsb_release)
        LOGGER.info('system uname %s' % self._sys_uname)

    def _flush_faucet_events(self):
        LOGGER.info('Flushing faucet event queue...')
        if self.faucet_events:
            while self.faucet_events.next_event():
                pass

    def _open_result_log(self):
        return open(self._RESULT_LOG_FILE, 'w')

    def _get_states(self):
        states = connected_host.pre_states() + self.config['test_list']
        return states + connected_host.post_states()

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
            'daq_run_id': str(self._daq_run_id)
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
            (dpid, port, target_mac) = self.faucet_events.as_port_learn(event)
            if dpid and port:
                self._handle_port_learn(dpid, port, target_mac)
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

        if port not in self._port_info:
            self._port_info[port] = PortInfo()

        if active != self._port_info[port].active:
            LOGGER.info('Port %s dpid %s is now %s', port, dpid, "active" if active else "inactive")
        if active:
            self._activate_port(port)
        else:
            port_info = self._port_info[port]
            if port_info.host and not port_info.flapping_start:
                port_info.flapping_start = time.time()
            if port_info.active:
                if port_info.mac and not port_info.flapping_start:
                    self._direct_port_traffic(port_info.mac, port, None)
                self._deactivate_port(port)
        self._send_heartbeat()

    def _activate_port(self, port):
        port_info = self._port_info[port]
        port_info.flapping_start = 0
        port_info.active = True

    def _deactivate_port(self, port):
        port_info = self._port_info[port]
        port_info.active = False

    def _direct_port_traffic(self, mac, port, target):
        self.network.direct_port_traffic(mac, port, target)

    def _handle_port_learn(self, dpid, port, target_mac):
        if self.network.is_device_port(dpid, port):
            LOGGER.info('Port %s dpid %s learned %s', port, dpid, target_mac)
            self._mac_port_map[target_mac] = port
            self._port_info[port].mac = target_mac
            self._target_set_trigger(port)
        else:
            LOGGER.debug('Port %s dpid %s learned %s (ignored)', port, dpid, target_mac)

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
        for target_port, target_host in self._get_port_hosts():
            try:
                if target_host.is_running():
                    all_idle = False
                    target_host.idle_handler()
                else:
                    self.target_set_complete(target_port, 'target set not active')
            except Exception as e:
                self.target_set_error(target_host.target_port, e)
        if not self.event_trigger:
            for target_port, port_info in self._port_info.items():
                if port_info.active and port_info.mac:
                    self._target_set_trigger(target_port)
                    all_idle = False
        if not self._get_running_ports() and not self.run_tests:
            if self.faucet_events and not self._linger_exit:
                self.shutdown()
            if self._linger_exit == 1:
                self._linger_exit = 2
                LOGGER.warning('Result linger on exit.')
            all_idle = False
        if all_idle:
            LOGGER.debug('No active device ports, waiting for trigger event...')

    def _reap_stale_ports(self):
        for port, port_info in copy.copy(self._port_info).items():
            if not port_info.flapping_start or not port_info.host:
                continue
            host = port_info.host
            timeout_sec = host.get_port_flap_timeout(host.test_name)
            if timeout_sec is None:
                timeout_sec = self._default_port_flap_timeout
            if (port_info.flapping_start + timeout_sec) <= time.time():
                exception = DaqException('port not active for %ds' % timeout_sec)
                self.target_set_error(port, exception)
                port_info.flapping_start = 0

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
        states = {p: h.state for p, h in self._get_port_hosts()}
        LOGGER.debug('Active target sets/state: %s', states)

    def _terminate(self):
        for target_port in self._get_running_ports():
            self.target_set_error(target_port, DaqException('terminated'))

    def _module_heartbeat(self):
        # Should probably be converted to a separate thread to timeout any blocking fn calls
        _ = [host.heartbeat() for _, host in self._get_port_hosts()]

    def main_loop(self):
        """Run main loop to execute tests"""

        try:
            monitor = stream_monitor.StreamMonitor(idle_handler=self._handle_system_idle,
                                                   loop_hook=self._loop_hook,
                                                   timeout_sec=20)  # Polling rate
            self.stream_monitor = monitor
            self.monitor_stream('faucet', self.faucet_events.sock, self._handle_faucet_events,
                                priority=10)
            if self.event_trigger:
                self._flush_faucet_events()
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

    def _target_set_trigger(self, target_port):
        target_active = target_port in self._port_info and self._port_info[target_port].active
        assert target_active, 'Target port %d not active' % target_port

        target_mac = self._port_info[target_port].mac
        assert target_mac, 'Target port %d triggered but not learned' % target_port

        if not self._system_active:
            LOGGER.warning('Target port %d ignored, system not active', target_port)
            return False

        if self._port_info[target_port].host:
            LOGGER.debug('Target port %d already triggered', target_port)
            return False

        if not self.run_tests:
            LOGGER.debug('Target port %d trigger suppressed', target_port)
            return False

        try:
            group_name = self.network.device_group_for(target_mac)
            gateway = self._activate_device_group(group_name, target_port)
            if gateway.activated:
                LOGGER.debug('Target port %d trigger ignored b/c activated gateway', target_port)
                return False
        except Exception as e:
            LOGGER.error('Target port %d target trigger error %s', target_port, str(e))
            if self.fail_mode:
                LOGGER.warning('Suppressing further tests due to failure.')
                self.run_tests = False
            return False

        target = {
            'port': target_port,
            'group': group_name,
            'fake': gateway.fake_target,
            'port_set': gateway.port_set,
            'mac': target_mac
        }

        # Stops all DHCP response initially
        # Selectively enables dhcp response at ipaddr stage based on dhcp mode
        gateway.execute_script('change_dhcp_response_time', target_mac, -1)
        gateway.attach_target(target_port, target)

        try:
            self.run_count += 1
            new_host = connected_host.ConnectedHost(self, gateway, target, self.config)
            self._port_info[target_port].host = new_host
            self._port_info[target_port].gateway = gateway
            LOGGER.info('Target port %d registered %s', target_port, target_mac)
            new_host.register_dhcp_ready_listener(self._dhcp_ready_listener)
            new_host.initialize()

            self._direct_port_traffic(target_mac, target_port, target)
            return True
        except Exception as e:
            self.target_set_error(target_port, e)

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

    def allocate_test_port(self, target_port):
        """Get the test port for the given target_port"""
        gateway = self._port_info[target_port].gateway
        return gateway.allocate_test_port()

    def release_test_port(self, target_port, test_port):
        """Release the given test port"""
        gateway = self._port_info[target_port].gateway
        return gateway.release_test_port(test_port)

    def _activate_device_group(self, group_name, target_port):
        if group_name in self._device_groups:
            existing = self._device_groups[group_name]
            LOGGER.debug('Gateway for existing device group %s is %s', group_name, existing.name)
            return existing
        set_num = self._find_gateway_set(target_port)
        LOGGER.info('Gateway for device group %s not found, initializing base %d...',
                    group_name, set_num)
        gateway = gateway_manager.Gateway(self, group_name, set_num, self.network)
        self._gateway_sets[set_num] = group_name
        self._device_groups[group_name] = gateway
        try:
            gateway.initialize()
        except Exception:
            LOGGER.error('Cleaning up from failed gateway initialization')
            LOGGER.debug('Clearing target %s gateway group %s for %s',
                         target_port, set_num, group_name)
            del self._gateway_sets[set_num]
            del self._device_groups[group_name]
            raise
        return gateway

    def ip_notify(self, state, target, gateway_set, exception=None):
        """Handle a DHCP / Static IP notification"""
        if exception:
            assert not target, 'unexpected exception with target'
            LOGGER.error('IP exception for gw%02d: %s', gateway_set, exception)
            LOGGER.exception(exception)
            self._terminate_gateway_set(gateway_set)
            return

        target_mac, target_ip, delta_sec = target['mac'], target['ip'], target['delta']
        LOGGER.info('IP notify %s is %s on gw%02d (%s/%d)', target_mac,
                    target_ip, gateway_set, state, delta_sec)

        if not target_mac:
            LOGGER.warning('IP target mac missing')
            return

        self._target_mac_ip[target_mac] = target_ip
        host = self._get_host_from_mac(target_mac)
        if host:
            self._ip_info[host] = (state, target, gateway_set)
            host.ip_notify(target_ip, state, delta_sec)
            self._check_and_activate_gateway(host)

    def _get_host_from_mac(self, mac):
        if mac not in self._mac_port_map:
            return None
        return self._port_info[self._mac_port_map[mac]].host

    def _get_port_hosts(self):
        return list({p: i.host for p, i in self._port_info.items() if i.host}.items())

    def _get_running_ports(self):
        return [p for p, i in self._port_info.items() if i.host]

    def _get_active_ports(self):
        return [p for p, i in self._port_info.items() if i.active]

    def _check_and_activate_gateway(self, host):
        # Host ready to be activated and DHCP happened / Static IP
        if host not in self._ip_info or host not in self._dhcp_ready:
            return
        state, target, gateway_set = self._ip_info[host]
        target_mac, target_ip, delta_sec = target['mac'], target['ip'], target['delta']
        (gateway, ready_devices) = self._should_activate_target(target_mac, target_ip, gateway_set)

        if not ready_devices:
            return

        if ready_devices is True:
            self._get_host_from_mac(target_mac).trigger(state, target_ip=target_ip,
                                                        delta_sec=delta_sec)
        else:
            self._activate_gateway(state, gateway, ready_devices, delta_sec)

    def _dhcp_ready_listener(self, host):
        self._dhcp_ready.add(host)
        self._check_and_activate_gateway(host)

    def _activate_gateway(self, state, gateway, ready_devices, delta_sec):
        gateway.activate()
        if len(ready_devices) > 1:
            state = 'group'
            delta_sec = -1
        for ready_mac in ready_devices:
            LOGGER.info('IP activating target %s', ready_mac)
            ready_host = self._get_host_from_mac(ready_mac)
            ready_ip = self._target_mac_ip[ready_mac]
            triggered = ready_host.trigger(state, target_ip=ready_ip, delta_sec=delta_sec)
            assert triggered, 'host %s not triggered' % ready_mac

    def _should_activate_target(self, target_mac, target_ip, gateway_set):
        target_host = self._get_host_from_mac(target_mac)
        if not target_host:
            LOGGER.warning('DHCP targets missing %s', target_mac)
            return False, False

        group_name = self._gateway_sets[gateway_set]
        gateway = self._device_groups[group_name]

        if gateway.activated:
            LOGGER.info('DHCP activation group %s already activated', group_name)
            return gateway, True

        if not target_host.notify_activate():
            LOGGER.info('DHCP device %s ignoring spurious notify', target_mac)
            return gateway, False

        ready_devices = gateway.target_ready(target_mac)
        group_size = self.network.device_group_size(group_name)

        remaining = group_size - len(ready_devices)
        if remaining and self.run_tests:
            LOGGER.info('DHCP waiting for %d additional members of group %s', remaining, group_name)
            return gateway, False

        hosts = map(self._get_host_from_mac, ready_devices)
        ready_trigger = all(map(lambda host: host.trigger_ready(), hosts))
        if not ready_trigger:
            LOGGER.info('DHCP device group %s not ready to trigger', group_name)
            return gateway, False

        return gateway, ready_devices

    def _terminate_gateway_set(self, gateway_set):
        assert gateway_set in self._gateway_sets, 'Gateway set %s not found'
        group_name = self._gateway_sets[gateway_set]
        gateway = self._device_groups[group_name]
        ports = [target['port'] for target in gateway.get_targets()]
        LOGGER.info('Terminating gateway group %s set %s, ports %s', group_name, gateway_set, ports)
        for target_port in ports:
            self.target_set_error(target_port, DaqException('terminated'))

    def _find_gateway_set(self, target_port):
        if target_port not in self._gateway_sets:
            return target_port
        for entry in range(1, self.MAX_GATEWAYS):
            if entry not in self._gateway_sets:
                return entry
        raise Exception('Could not allocate open gateway set')

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

    def target_set_error(self, target_port, exception):
        """Handle an error in the target port set"""
        running = bool(target_port in self._port_info and self._port_info[target_port].host)
        LOGGER.error('Target port %d running %s exception: %s', target_port, running, exception)
        LOGGER.exception(exception)
        if running:
            target_host = self._port_info[target_port].host
            target_host.record_result(target_host.test_name, exception=exception)
            self.target_set_complete(target_port, str(exception))
        else:
            stack = ''.join(
                traceback.format_exception(etype=type(exception), value=exception,
                                           tb=exception.__traceback__))
            self._target_set_finalize(target_port,
                                      {'exception': {'exception': str(exception),
                                                     'traceback': stack}},
                                      str(exception))
            self._detach_gateway(target_port)

    def target_set_complete(self, target_port, reason):
        """Handle completion of a target_set"""
        target_host = self._port_info[target_port].host
        self._target_set_finalize(target_port, target_host.results, reason)
        self._target_set_cancel(target_port)

    def _target_set_finalize(self, target_port, result_set, reason):
        results = self._combine_result_set(target_port, result_set)
        LOGGER.info('Target port %d finalize: %s (%s)', target_port, results, reason)
        if self.result_log:
            self.result_log.write('%02d: %s\n' % (target_port, results))
            self.result_log.flush()

        suppress_tests = self.fail_mode or self.result_linger
        if results and suppress_tests:
            LOGGER.warning('Suppressing further tests due to failure.')
            self.run_tests = False
            if self.result_linger:
                self._linger_exit = 1
        self._result_sets[target_port] = result_set

    def _target_set_cancel(self, target_port):
        target_host = self._port_info[target_port].host
        if target_host:
            self._port_info[target_port].host = None
            target_mac = self._port_info[target_port].mac
            del self._mac_port_map[target_mac]
            target_gateway = self._port_info[target_port].gateway
            LOGGER.info('Target port %d cancel %s (#%d/%s).',
                        target_port, target_mac, self.run_count, self.run_limit)
            results = self._combine_result_set(target_port, self._result_sets.get(target_port))
            this_result_linger = results and self.result_linger
            target_gateway_linger = target_gateway and target_gateway.result_linger
            if target_gateway_linger or this_result_linger:
                LOGGER.warning('Target port %d result_linger: %s', target_port, results)
                self._activate_port(target_port)
                target_gateway.result_linger = True
            else:
                self._direct_port_traffic(target_mac, target_port, None)
                target_host.terminate('_target_set_cancel', trigger=False)
                if target_gateway:
                    self._detach_gateway(target_port)
            if self.run_limit and self.run_count >= self.run_limit and self.run_tests:
                LOGGER.warning('Suppressing future tests because run limit reached.')
                self.run_tests = False
            if self.single_shot and self.run_tests:
                LOGGER.warning('Suppressing future tests because test done in single shot.')
                self.run_tests = False
        LOGGER.info('Remaining target sets: %s', self._get_running_ports())

    def _detach_gateway(self, target_port):
        target_gateway = self._port_info[target_port].gateway
        if not target_gateway:
            return
        self._port_info[target_port].gateway = None
        target_mac = self._port_info[target_port].mac
        if not target_gateway.detach_target(target_port):
            LOGGER.info('Retiring target gateway %s, %s, %s, %s',
                        target_port, target_mac, target_gateway.name, target_gateway.port_set)
            group_name = self.network.device_group_for(target_mac)
            del self._device_groups[group_name]
            del self._gateway_sets[target_gateway.port_set]
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
                results.append('%02d:%s:%s' % (set_key, name, status))
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
        _ = [host.reload_config() for _, host in self._get_port_hosts()]

    def _load_base_config(self, register=True):
        base = self.configurator.load_and_merge({}, self.config.get('base_conf'))
        site_config = self.configurator.load_config(self.config.get('site_path'),
                                                    self._MODULE_CONFIG, optional=True)
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
