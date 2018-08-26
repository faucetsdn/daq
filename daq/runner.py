"""Main test runner for DAQ"""

import logging
import os
import time

import faucet_event_client
import gateway as gateway_manager
import gcp
import host as connected_host
import network
import stream_monitor

LOGGER = logging.getLogger('runner')
RESULT_LOG_FILE = 'inst/result.log'

class DAQRunner():
    """Main runner class controlling DAQ. Primarily mediates between
    faucet events, connected hosts (to test), and gcp for logging. This
    class owns the main event loop and shards out work to subclasses."""

    MAX_GATEWAYS = 10

    def __init__(self, config):
        self.config = config
        self.port_targets = {}
        self.port_gateways = {}
        self.mac_targets = {}
        self.result_sets = {}
        self.active_ports = {}
        self._device_groups = {}
        self._gateway_sets = {}
        self.gcp = gcp.GcpManager(self.config)
        self.description = config.get('site_description', '').strip("\"")
        self.version = os.environ['DAQ_VERSION']
        self.network = network.TestNetwork(config)
        self.result_linger = config.get('result_linger', False)
        self.faucet_events = None
        self.single_shot = config.get('single_shot')
        self.event_trigger = config.get('event_trigger')
        self.fail_mode = config.get('fail_mode')
        self.run_tests = True
        self.stream_monitor = None
        self.exception = None
        self.run_count = 0
        self.run_limit = int(config.get('run_limit', 0))
        self.result_log = self._open_result_log()

    def _flush_faucet_events(self):
        LOGGER.info('Flushing faucet event queue...')
        while self.faucet_events.next_event():
            pass

    def _open_result_log(self):
        return open(RESULT_LOG_FILE, 'w')

    def _send_heartbeat(self):
        self.gcp.publish_message('daq_runner', {
            'name': 'status',
            'tests': connected_host.ConnectedHost.TEST_ORDER,
            'ports': self.active_ports.keys(),
            'description': self.description,
            'version': self.version,
            'timestamp': int(time.time()),
        })

    def _port_control(self, message):
        LOGGER.info('port_control %s', message)

    def initialize(self):
        """Initialize DAQ instance"""
        self._send_heartbeat()

        self.network.initialize()

        LOGGER.debug("Attaching event channel...")
        self.faucet_events = faucet_event_client.FaucetEventClient()
        self.faucet_events.connect(os.getenv('FAUCET_EVENT_SOCK'))

        LOGGER.info("Waiting for system to settle...")
        time.sleep(3)

        LOGGER.debug('Done with initialization')

    def cleanup(self):
        """Cleanup instance"""
        try:
            LOGGER.debug("Stopping network...")
            self.network.stop()
        except Exception as e:
            LOGGER.error('Exception: %s', e)
        if self.result_log:
            self.result_log.close()
            self.result_log = None
        LOGGER.info("Done with runner.")

    def add_host(self, *args, **kwargs):
        """Add a host with the given parameters"""
        return self.network.add_host(*args, **kwargs)

    def remove_host(self, host):
        """Remove the given host"""
        return self.network.remove_host(host)

    def get_host_interface(self, host):
        """Get the internal interface for the host"""
        return self.network.get_host_interface(host)

    def _handle_faucet_event(self):
        while True:
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

    def _handle_port_state(self, dpid, port, active):
        LOGGER.debug('Port dpid %s port %s is active %s', dpid, port, active)
        if self.network.is_device_port(dpid, port):
            if active:
                self.active_ports[port] = True
            else:
                if port in self.port_targets:
                    self.target_set_complete(self.port_targets[port])
                if port in self.active_ports:
                    if self.active_ports[port] is not True:
                        self.network.direct_port_traffic(self.active_ports[port], None)
                    del self.active_ports[port]

    def _handle_port_learn(self, dpid, port, target_mac):
        LOGGER.debug('Port dpid %s port %s is mac %s', dpid, port, target_mac)
        if self.network.is_device_port(dpid, port):
            self.active_ports[port] = target_mac
            self._target_set_trigger(port)

    def _handle_system_idle(self):
        all_idle = True
        # Iterate over copy of list to prevent fail-on-modification.
        for target_set in list(self.port_targets.values()):
            try:
                if target_set.is_active():
                    all_idle = False
                    target_set.idle_handler()
                else:
                    self.target_set_complete(target_set)
            except Exception as e:
                self.target_set_error(target_set.target_port, e)
        if not self.event_trigger:
            for target_port in self.active_ports:
                if self.active_ports[target_port] is not True:
                    self._target_set_trigger(target_port)
                    all_idle = False
        if not self.port_targets and not self.run_tests:
            if self.faucet_events:
                LOGGER.warning('No active ports remaining: ending test run.')
                self.monitor_forget(self.faucet_events.sock)
                self.faucet_events.disconnect()
                self.faucet_events = None
            all_idle = False
        if all_idle:
            LOGGER.debug('No active device ports, waiting for trigger event...')

    def _loop_hook(self):
        states = {}
        for key in self.port_targets:
            states[key] = self.port_targets[key].state
        LOGGER.debug('Active target sets/state: %s', states)

    def _terminate(self):
        target_set_keys = self.port_targets.keys()
        for key in target_set_keys:
            self.port_targets[key].terminate()

    def main_loop(self):
        """Run main loop to execute tests"""

        try:
            monitor = stream_monitor.StreamMonitor(idle_handler=self._handle_system_idle,
                                                   loop_hook=self._loop_hook)
            self.stream_monitor = monitor
            self.monitor_stream('faucet', self.faucet_events.sock, self._handle_faucet_event)
            if self.event_trigger:
                self._flush_faucet_events()
            LOGGER.info('Entering main event loop.')
            self.stream_monitor.event_loop()
        except Exception as e:
            LOGGER.error('Event loop exception: %s', e)
            LOGGER.exception(e)
            self.exception = e
        except KeyboardInterrupt as e:
            LOGGER.error('Keyboard Interrupt')
            LOGGER.exception(e)

        if self.config.get('use_console'):
            LOGGER.info('Dropping into interactive command line')
            self.network.cli()

        self._terminate()

    def _target_set_trigger(self, target_port):
        assert target_port in self.active_ports, 'Target port %d not active' % target_port

        target_mac = self.active_ports[target_port]
        assert target_mac is not True, 'Target port %d triggered but not learned' % target_port

        if target_port in self.port_targets:
            LOGGER.debug('Target port %d already active', target_port)
            return False

        if not self.run_tests:
            LOGGER.debug('Target port %d trigger ignored', target_port)
            return False

        try:
            group_name = self.network.device_group_for(target_mac)
            gateway = self._activate_device_group(group_name, target_port)
            target = {
                'port': target_port,
                'group': group_name,
                'fake': gateway.fake_target,
                'range': gateway.get_port_range(),
                'mac': target_mac
            }
            gateway.attach_target(target_port, target)
        except Exception as e:
            LOGGER.error('Target port %d gateway error %s', target_port, str(e))
            return False

        try:
            new_host = connected_host.ConnectedHost(self, gateway.host, target, self.config)
            self.mac_targets[target_mac] = new_host
            self.port_targets[target_port] = new_host
            self.port_gateways[target_port] = gateway
            LOGGER.info('Target port %d registered %s', target_port, target_mac)

            new_host.initialize()

            self.network.direct_port_traffic(target_mac, target)

            self._send_heartbeat()
            return True
        except Exception as e:
            self.target_set_error(target_port, e)

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
            return existing
        set_num = self._find_gateway_set(target_port)
        LOGGER.info('Gateway for device group %s not found, initializing base %d...',
                    group_name, set_num)
        gateway = gateway_manager.Gateway(self, group_name, set_num, self.network)
        gateway.initialize()
        self._gateway_sets[set_num] = group_name
        self._device_groups[group_name] = gateway
        return gateway

    def dhcp_notify(self, state, target=None, exception=None, gateway_set=None):
        """Handle a DHCP notificaiton"""
        if exception:
            LOGGER.error('DHCP exception set %s: %s', gateway_set, exception)
            LOGGER.exception(exception)
            self._terminate_gateway_set(gateway_set)
            return
        target_mac = target['mac']
        target_ip = target['ip']
        LOGGER.info('DHCP notify %s/%s', target_ip, target_mac)
        if target_mac in self.mac_targets:
            target_host = self.mac_targets[target_mac]
            target_host.dhcp_result(state, target_ip=target_ip, exception=exception)

    def _terminate_gateway_set(self, gateway_set):
        group_name = self._gateway_sets[gateway_set]
        gateway = self._device_groups[group_name]
        ports = [target['port'] for target in gateway.get_targets()]
        LOGGER.info('Terminating gateway group %s set %s, ports %s', group_name, gateway_set, ports)
        for target_port in ports:
            self.target_set_complete(self.port_targets[target_port])

    def _find_gateway_set(self, target_port):
        if target_port not in self._gateway_sets:
            return target_port
        for entry in range(1, self.MAX_GATEWAYS):
            if entry not in self._gateway_sets:
                return entry
        raise Exception('Could not allocate open gateway set')

    def ping_test(self, src, dst, src_addr=None):
        """Test ping between hosts"""
        dst_name = dst if isinstance(dst, str) else dst.name
        dst_ip = dst if isinstance(dst, str) else dst.IP()
        from_msg = ' from %s' % src_addr if src_addr else ''
        LOGGER.info("Test ping %s->%s%s", src.name, dst_name, from_msg)
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
        LOGGER.warning('Target port %d (%s) exception: %s', target_port, active, e)
        LOGGER.exception(e)
        if active:
            target_set = self.port_targets[target_port]
            target_set.record_result(target_set.test_name, exception=e)
            self.target_set_complete(target_set)
        else:
            self._target_set_finalize(target_port, {'exception': {'exception': str(e)}})

    def target_set_complete(self, target_set):
        """Handle completion of a target_set"""
        target_port = target_set.target_port
        self._target_set_finalize(target_port, target_set.results)
        self._target_set_cancel(target_port)

    def _target_set_finalize(self, target_port, result_set):
        results = self._combine_result_set(target_port, result_set)
        LOGGER.info('Target port %d complete: %s', target_port, results)
        if self.result_log:
            self.result_log.write('%02d: %s\n' % (target_port, results))
            self.result_log.flush()
        if results and self.fail_mode:
            LOGGER.warning('Suppressing further tests due to failure.')
            self.run_tests = False
        self.result_sets[target_port] = result_set

    def _target_set_cancel(self, target_port):
        if target_port in self.port_targets:
            target_host = self.port_targets[target_port]
            del self.port_targets[target_port]
            target_gateway = self.port_gateways[target_port]
            del self.port_gateways[target_port]
            target_mac = self.active_ports[target_port]
            del self.mac_targets[target_mac]
            self.run_count += 1
            LOGGER.info('Target port %d cancel %s (#%d/%s).',
                        target_port, target_mac, self.run_count, self.run_limit)
            results = self._combine_result_set(target_port, self.result_sets[target_port])
            if results and self.result_linger:
                LOGGER.warning('Target port %d result_linger: %s', target_port, results)
                self.active_ports[target_port] = True
            else:
                target_host.terminate(trigger=False)
                self._detach_gateway(target_port, target_mac, target_gateway)
            if self.run_limit and self.run_count >= self.run_limit and self.run_tests:
                LOGGER.warning('Suppressing future tests because run limit reached.')
                self.run_tests = False
            if self.single_shot and self.run_tests:
                LOGGER.warning('Suppressing future tests because test done in single shot.')
                self.run_tests = False
        LOGGER.info('Remaining target sets: %s', self.port_targets.keys())

    def _detach_gateway(self, target_port, target_mac, target_gateway):
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

    def _extract_exception(self, result):
        key = 'exception'
        return key if key in result and result[key] is not None else None

    def _combine_results(self):
        results = []
        for result_set_key in self.result_sets:
            result_set = self.result_sets[result_set_key]
            results.extend(self._combine_result_set(result_set_key, result_set))
        return results

    def _combine_result_set(self, set_key, result_sets):
        results = []
        for result_set_key in result_sets:
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
        exception = self.exception
        failures = self._combine_results()
        if failures:
            LOGGER.error('Test failures: %s', failures)
        if exception:
            LOGGER.error('Exiting b/c of exception: %s', exception)
        if failures or exception:
            return 1
        return 0
