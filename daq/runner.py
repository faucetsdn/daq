"""Main test runner for DAQ"""

import copy
import logging
import os
import re
import threading
import time
import traceback

import configurator
import faucet_event_client
import gateway as gateway_manager
import gcp
import host as connected_host
import network
import stream_monitor
import wrappers

LOGGER = logging.getLogger('runner')


class DAQRunner:
    """Main runner class controlling DAQ. Primarily mediates between
    faucet events, connected hosts (to test), and gcp for logging. This
    class owns the main event loop and shards out work to subclasses."""

    MAX_GATEWAYS = 10
    _MODULE_CONFIG = 'module_config.json'
    _RUNNER_CONFIG_PATH = 'runner/setup'
    _DEFAULT_TESTS_FILE = 'misc/host_tests.conf'
    _RESULT_LOG_FILE = 'inst/result.log'

    def __init__(self, config):
        self.config = config
        self.port_targets = {}
        self.port_gateways = {}
        self.mac_targets = {}
        self.result_sets = {}
        self._active_ports = {}
        self._device_groups = {}
        self._gateway_sets = {}
        self._target_mac_ip = {}
        self._callback_queue = []
        self._callback_lock = threading.Lock()
        self.gcp = gcp.GcpManager(self.config, self._queue_callback)
        self._base_config = self._load_base_config()
        self.description = config.get('site_description', '').strip('\"')
        self.version = os.environ['DAQ_VERSION']
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
        self.result_log = self._open_result_log()
        self._system_active = False

        test_list = self._get_test_list(config.get('host_tests', self._DEFAULT_TESTS_FILE), [])
        if self.config.get('keep_hold'):
            test_list.append('hold')
        config['test_list'] = test_list
        LOGGER.info('Configured with tests %s', config['test_list'])

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
        self.gcp.publish_message('daq_runner', 'heartbeat', {
            'name': 'status',
            'states': self._get_states(),
            'ports': list(self._active_ports.keys()),
            'description': self.description,
            'version': self.version,
            'timestamp': int(time.time()),
        })

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
            LOGGER.error('Exception: %s', e)
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
            LOGGER.debug('Faucet event %s', event)
            if not event:
                break
            (dpid, port, active) = self.faucet_events.as_port_state(event)
            if dpid and port:
                self._handle_port_state(dpid, port, active)
            (dpid, port, target_mac) = self.faucet_events.as_port_learn(event)
            if dpid and port:
                self._handle_port_learn(dpid, port, target_mac)
            (dpid, restart_type) = self.faucet_events.as_config_change(event)
            if dpid is not None:
                LOGGER.debug('dp_id %d restart %s', dpid, restart_type)

    def _handle_port_state(self, dpid, port, active):
        if self.network.is_system_port(dpid, port):
            LOGGER.info('System port %s on dpid %s is active %s', port, dpid, active)
            self._system_active = active
            return
        if not self.network.is_device_port(dpid, port):
            LOGGER.debug('Unknown port %s on dpid %s is active %s', port, dpid, active)
            return

        if active != (port in self._active_ports):
            LOGGER.info('Port %s dpid %s is now active %s', port, dpid, active)
            if active:
                connected_host.ConnectedHost.clear_port(self.gcp, port)
        if active:
            if not self._active_ports.get(port):
                self._activate_port(port, True)
        else:
            if port in self.port_targets:
                self.target_set_complete(self.port_targets[port], 'port not active')
            if port in self._active_ports:
                if self._active_ports[port] is not True:
                    self._direct_port_traffic(self._active_ports[port], port, None)
                self._activate_port(port, None)

    def _activate_port(self, port, state):
        if state:
            self._active_ports[port] = state
        elif port in self._active_ports:
            del self._active_ports[port]

    def _direct_port_traffic(self, mac, port, target):
        self.network.direct_port_traffic(mac, port, target)

    def _handle_port_learn(self, dpid, port, target_mac):
        if self.network.is_device_port(dpid, port):
            LOGGER.info('Port %s dpid %s learned %s', port, dpid, target_mac)
            self._activate_port(port, target_mac)
            self._target_set_trigger(port)
        else:
            LOGGER.debug('Port %s dpid %s learned %s', port, dpid, target_mac)

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
        # Iterate over copy of list to prevent fail-on-modification.
        for target_set in list(self.port_targets.values()):
            try:
                if target_set.is_running():
                    all_idle = False
                    target_set.idle_handler()
                else:
                    self.target_set_complete(target_set, 'target set not active')
            except Exception as e:
                self.target_set_error(target_set.target_port, e)
        if not self.event_trigger:
            for target_port in self._active_ports:
                if self._active_ports[target_port] is not True:
                    self._target_set_trigger(target_port)
                    all_idle = False
        if not self.port_targets and not self.run_tests:
            if self.faucet_events and not self._linger_exit:
                self.shutdown()
            if self._linger_exit == 1:
                self._linger_exit = 2
                LOGGER.warning('Result linger on exit.')
            all_idle = False
        if all_idle:
            LOGGER.debug('No active device ports, waiting for trigger event...')

    def shutdown(self):
        """Shutdown this runner by closing all active components"""
        ports = list(self._active_ports.keys())
        for port in ports:
            self._activate_port(port, False)
        self.monitor_forget(self.faucet_events.sock)
        self.faucet_events.disconnect()
        self.faucet_events = None
        count = self.stream_monitor.log_monitors()
        LOGGER.warning('No active ports remaining (%d monitors), ending test run.', count)

    def _loop_hook(self):
        self._handle_queued_events()
        states = {}
        for key in self.port_targets:
            states[key] = self.port_targets[key].state
        LOGGER.debug('Active target sets/state: %s', states)

    def _terminate(self):
        target_set_keys = list(self.port_targets.keys())
        for key in target_set_keys:
            self.port_targets[key].terminate()

    def main_loop(self):
        """Run main loop to execute tests"""

        try:
            monitor = stream_monitor.StreamMonitor(idle_handler=self._handle_system_idle,
                                                   loop_hook=self._loop_hook)
            self.stream_monitor = monitor
            self.monitor_stream('faucet', self.faucet_events.sock, self._handle_faucet_events)
            if self.event_trigger:
                self._flush_faucet_events()
            LOGGER.info('Entering main event loop.')
            LOGGER.info('See docs/troubleshooting.md if this blocks for more than a few minutes.')
            self.stream_monitor.event_loop()
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
        assert target_port in self._active_ports, 'Target port %d not active' % target_port

        target_mac = self._active_ports[target_port]
        assert target_mac is not True, 'Target port %d triggered but not learned' % target_port

        if not self._system_active:
            LOGGER.warning('Target port %d ignored, system not active', target_port)
            return False

        if target_port in self.port_targets:
            LOGGER.debug('Target port %d already active', target_port)
            return False

        if not self.run_tests:
            LOGGER.debug('Target port %d trigger ignored', target_port)
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
        gateway.attach_target(target_port, target)

        try:
            self.run_count += 1
            new_host = connected_host.ConnectedHost(self, gateway.host, target, self.config)
            self.mac_targets[target_mac] = new_host
            self.port_targets[target_port] = new_host
            self.port_gateways[target_port] = gateway
            LOGGER.info('Target port %d registered %s', target_port, target_mac)

            new_host.initialize()

            self._direct_port_traffic(target_mac, target_port, target)

            self._send_heartbeat()
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
        gateway = self.port_gateways[target_port]
        return gateway.allocate_test_port()

    def release_test_port(self, target_port, test_port):
        """Release the given test port"""
        gateway = self.port_gateways[target_port]
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

    def dhcp_notify(self, state, target, gateway_set, exception=None):
        """Handle a DHCP notification"""
        if exception or not target:
            LOGGER.error('DHCP exception for gw%02d: %s', gateway_set, exception)
            LOGGER.exception(exception)
            self._terminate_gateway_set(gateway_set)
            return

        target_mac = target['mac']
        target_ip = target['ip']
        delta_sec = target['delta']
        LOGGER.info('DHCP notify %s is %s on gw%02d (%s/%s/%d)', target_mac,
                    target_ip, gateway_set, state, str(exception), delta_sec)

        if not target_mac:
            LOGGER.warning('DHCP target mac missing')
            return

        self._target_mac_ip[target_mac] = target_ip

        (gateway, ready_devices) = self._should_activate_target(target_mac, target_ip, gateway_set)

        if not ready_devices:
            return

        if ready_devices is True:
            self.mac_targets[target_mac].trigger(state, target_ip=target_ip, delta_sec=delta_sec)
            return

        self._activate_gateway(state, gateway, ready_devices, delta_sec)

    def _activate_gateway(self, state, gateway, ready_devices, delta_sec):
        gateway.activate()
        if len(ready_devices) > 1:
            state = 'group'
            delta_sec = -1
        for ready_mac in ready_devices:
            LOGGER.info('DHCP activating target %s', ready_mac)
            ready_host = self.mac_targets[ready_mac]
            ready_ip = self._target_mac_ip[ready_mac]
            triggered = ready_host.trigger(state, target_ip=ready_ip, delta_sec=delta_sec)
            assert triggered, 'host %s not triggered' % ready_mac

    def _should_activate_target(self, target_mac, target_ip, gateway_set):
        if target_mac not in self.mac_targets:
            LOGGER.warning('DHCP targets missing %s', target_mac)
            return False, False

        group_name = self._gateway_sets[gateway_set]
        gateway = self._device_groups[group_name]

        if gateway.activated:
            LOGGER.info('DHCP activation group %s already activated', group_name)
            return gateway, True

        target_host = self.mac_targets[target_mac]
        if not target_host.notify_activate():
            LOGGER.info('DHCP device %s ignoring spurious notify', target_mac)
            return gateway, False

        ready_devices = gateway.target_ready(target_mac)
        group_size = self.network.device_group_size(group_name)

        remaining = group_size - len(ready_devices)
        if remaining and self.run_tests:
            LOGGER.info('DHCP waiting for %d additional members of group %s', remaining, group_name)
            return gateway, False

        ready_trigger = True
        for ready_mac in ready_devices:
            ready_host = self.mac_targets[ready_mac]
            ready_trigger = ready_trigger and ready_host.trigger_ready()
        if not ready_trigger:
            LOGGER.warning('DHCP device group %s not ready to trigger', group_name)
            return gateway, False

        return gateway, ready_devices

    def _terminate_gateway_set(self, gateway_set):
        if gateway_set not in self._gateway_sets:
            LOGGER.warning('Gateway set %s not found in %s', gateway_set, self._gateway_sets)
            return
        group_name = self._gateway_sets[gateway_set]
        gateway = self._device_groups[group_name]
        ports = [target['port'] for target in gateway.get_targets()]
        LOGGER.info('Terminating gateway group %s set %s, ports %s', group_name, gateway_set, ports)
        for target_port in ports:
            self.target_set_complete(self.port_targets[target_port], 'gateway set terminating')

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

    def target_set_error(self, target_port, e):
        """Handle an error in the target port set"""
        active = target_port in self.port_targets
        err_str = str(e)
        # pylint: disable=no-member
        message = err_str if isinstance(e, wrappers.DaqException) else \
                  ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
        LOGGER.error('Target port %d active %s exception: %s', target_port, active, message)
        self._detach_gateway(target_port)
        if active:
            target_set = self.port_targets[target_port]
            target_set.record_result(target_set.test_name, exception=err_str)
            self.target_set_complete(target_set, err_str)
        else:
            self._target_set_finalize(target_port, {'exception': {'exception': err_str}}, err_str)

    def target_set_complete(self, target_set, reason):
        """Handle completion of a target_set"""
        target_port = target_set.target_port
        self._target_set_finalize(target_port, target_set.results, reason)
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
        self.result_sets[target_port] = result_set

    def _target_set_cancel(self, target_port):
        if target_port in self.port_targets:
            target_host = self.port_targets[target_port]
            del self.port_targets[target_port]
            target_gateway = self.port_gateways.get(target_port)
            target_mac = self._active_ports[target_port]
            del self.mac_targets[target_mac]
            LOGGER.info('Target port %d cancel %s (#%d/%s).',
                        target_port, target_mac, self.run_count, self.run_limit)
            results = self._combine_result_set(target_port, self.result_sets[target_port])
            this_result_linger = results and self.result_linger
            target_gateway_linger = target_gateway and target_gateway.result_linger
            if target_gateway_linger or this_result_linger:
                LOGGER.warning('Target port %d result_linger: %s', target_port, results)
                self._activate_port(target_port, True)
                target_gateway.result_linger = True
            else:
                self._direct_port_traffic(target_mac, target_port, None)
                target_host.terminate(trigger=False)
                if target_gateway:
                    self._detach_gateway(target_port)
            if self.run_limit and self.run_count >= self.run_limit and self.run_tests:
                LOGGER.warning('Suppressing future tests because run limit reached.')
                self.run_tests = False
            if self.single_shot and self.run_tests:
                LOGGER.warning('Suppressing future tests because test done in single shot.')
                self.run_tests = False
        LOGGER.info('Remaining target sets: %s', list(self.port_targets.keys()))

    def _detach_gateway(self, target_port):
        target_gateway = self.port_gateways[target_port]
        del self.port_gateways[target_port]
        target_mac = self._active_ports[target_port]
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

    @staticmethod
    def _extract_exception(result):
        value = result.get('exception', None)
        return None if value == 'None' else value

    def _combine_results(self):
        results = []
        for result_set_key in self.result_sets:
            result_set = self.result_sets[result_set_key]
            results.extend(self._combine_result_set(result_set_key, result_set))
        return results

    def _combine_result_set(self, set_key, result_sets):
        results = []
        result_set_keys = list(result_sets)
        result_set_keys.sort()
        for result_set_key in result_set_keys:
            result = result_sets[result_set_key]
            exception = self._extract_exception(result)
            code_string = result['code'] if 'code' in result else None
            code = int(code_string) if code_string else 0
            name = result['name'] if 'name' in result else result_set_key
            status = exception if exception else code if name != 'fail' else not code
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
        configurator.write_config(self.config.get('site_path'), self._MODULE_CONFIG, new_config)
        self._base_config = self._load_base_config(register=False)
        self._publish_runner_config(self._base_config)
        for target_port in self.port_targets:
            self.port_targets[target_port].reload_config()

    def _load_base_config(self, register=True):
        base = {}
        configurator.load_and_merge(base, self.config.get('base_conf'))
        site_config = configurator.load_config(self.config.get('site_path'), self._MODULE_CONFIG)
        if register:
            self.gcp.register_config(self._RUNNER_CONFIG_PATH, site_config,
                                     self._base_config_changed)
        configurator.merge_config(base, site_config)
        return base

    def get_base_config(self):
        """Get the base configuration for this install"""
        return copy.deepcopy(self._base_config)

    def _publish_runner_config(self, loaded_config):
        result = {
            'timestamp': gcp.get_timestamp(),
            'config': loaded_config
        }
        self.gcp.publish_message('daq_runner', 'runner_config', result)
