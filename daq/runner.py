"""Main test runner for DAQ"""

import logging
import os
import time

from faucet_event_client import FaucetEventClient
from stream_monitor import StreamMonitor
from host import ConnectedHost
from network import TestNetwork
from gcp import GcpManager

LOGGER = logging.getLogger('runner')

class DAQRunner(object):
    """Main runner class controlling DAQ. Primarily mediates between
    faucet events, connected hosts (to test), and gcp for logging. This
    class owns the main event loop and shards out work to subclasses."""

    config = None
    target_sets = None
    active_ports = None
    result_sets = None
    gcp = None
    description = None
    version = None
    faucet_events = None
    flap_ports = None
    event_start = None
    monitor = None
    one_shot = None
    exception = None
    network = None

    def __init__(self, config):
        self.config = config
        self.target_sets = {}
        self.result_sets = {}
        self.active_ports = {}
        self.gcp = GcpManager(self.config)
        raw_description = config.get('site_description', '')
        self.description = raw_description.strip("\"")
        self.version = os.environ['DAQ_VERSION']
        self.network = TestNetwork(config)
        self.result_linger = config.get('result_linger', False)

    def _flush_faucet_events(self):
        LOGGER.info('Flushing faucet event queue...')
        while self.faucet_events.next_event():
            pass

    def _send_heartbeat(self):
        self.gcp.publish_message('daq_runner', {
            'name': 'status',
            'tests': ConnectedHost.TEST_ORDER,
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

        LOGGER.info("Starting faucet...")
        output = self.network.cmd('cmd/faucet && echo SUCCESS')
        if not output.strip().endswith('SUCCESS'):
            LOGGER.info('Faucet output: %s', output)
            assert False, 'Faucet startup failed'

        LOGGER.debug("Attaching event channel...")
        self.faucet_events = FaucetEventClient()
        self.faucet_events.connect(os.getenv('FAUCET_EVENT_SOCK'))

        LOGGER.info("Waiting for system to settle...")
        time.sleep(3)

        LOGGER.debug('Done with initialization')

    def cleanup(self):
        """Cleanup instance"""
        try:
            LOGGER.debug("Stopping faucet...")
            self.network.cmd('docker kill daq-faucet')
        except Exception as e:
            LOGGER.error('Exception: %s', e)
        try:
            LOGGER.debug("Stopping network...")
            self.network.stop()
        except Exception as e:
            LOGGER.error('Exception: %s', e)
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
            LOGGER.debug('Port state is dpid %s port %s active %s', dpid, port, active)
            if self.network.is_device_port(dpid, port):
                if active:
                    self.active_ports[port] = True
                    self._trigger_target_set(port)
                else:
                    if port in self.active_ports:
                        del self.active_ports[port]
                    self._cancel_target_set(port, removed=True)

    def _handle_system_idle(self):
        for target_set in self.target_sets.values():
            try:
                target_set.idle_handler()
            except Exception as e:
                self.target_set_error(target_set.port_set, e)
        if not self.event_start and not self.one_shot:
            for port_set in self.active_ports:
                if self.active_ports[port_set] and port_set not in self.target_sets:
                    self._trigger_target_set(port_set)

    def _loop_hook(self):
        states = {}
        for key in self.target_sets:
            states[key] = self.target_sets[key].state
        LOGGER.debug('Active target sets/state: %s', states)

    def _terminate(self):
        target_set_keys = self.target_sets.keys()
        for key in target_set_keys:
            self.target_sets[key].terminate()

    def main_loop(self):
        """Run main loop to execute tests"""
        self.one_shot = self.config.get('s')
        self.flap_ports = self.config.get('f')
        self.event_start = self.config.get('e')
        use_console = self.config.get('c')

        if self.flap_ports:
            self.network.flap_interface_ports()

        try:
            self.monitor = StreamMonitor(idle_handler=self._handle_system_idle,
                                         loop_hook=self._loop_hook)
            self.monitor_stream('faucet', self.faucet_events.sock, self._handle_faucet_event)
            if self.event_start:
                self._flush_faucet_events()
            LOGGER.info('Entering main event loop.')
            self.monitor.event_loop()
        except Exception as e:
            LOGGER.error('Event loop exception: %s', e)
            LOGGER.exception(e)
            self.exception = e
        except KeyboardInterrupt as e:
            LOGGER.error('Keyboard Interrupt')
            LOGGER.exception(e)

        keyboard_console = not self.one_shot and not self.exception
        if use_console or keyboard_console:
            LOGGER.info('Dropping into interactive command line')
            self.network.cli()

        self._terminate()

    def _trigger_target_set(self, port_set):
        assert port_set not in self.target_sets, 'target set %d already exists' % port_set
        try:
            LOGGER.debug('Trigger target set %d', port_set)
            self.target_sets[port_set] = ConnectedHost(self, port_set, self.config)
            self.target_sets[port_set].initialize()
            self._send_heartbeat()
        except Exception as e:
            self.target_set_error(port_set, e)

    def target_set_error(self, port_set, e):
        """Handle an error in the target port set"""
        LOGGER.info('Set %d exception: %s', port_set, e)
        if port_set in self.target_sets:
            target_set = self.target_sets[port_set]
            target_set.record_result(target_set.test_name, exception=e)
            self.target_set_complete(target_set)
        else:
            self._target_set_finalize(port_set, {'exception': str(e)})

    def target_set_complete(self, target_set):
        """Handle completion of a target_set"""
        port_set = target_set.port_set
        self._target_set_finalize(port_set, target_set.results)
        if self.result_linger:
            LOGGER.info('Set %d linger', port_set)
        else:
            self._cancel_target_set(port_set)

    def _target_set_finalize(self, port_set, results):
        LOGGER.info('Set %d complete, %d results', port_set, len(results))
        self.result_sets[port_set] = results
        LOGGER.info('Remaining sets: %s', self.target_sets.keys())

    def _cancel_target_set(self, port_set, removed=False):
        if port_set in self.target_sets:
            target_set = self.target_sets[port_set]
            del self.target_sets[port_set]
            target_set.terminate(trigger=False, removed=removed)
            LOGGER.info('Set %d cancelled (removed %s).', port_set, removed)
            if not self.target_sets and self.one_shot:
                self.monitor_forget(self.faucet_events.sock)

    def monitor_stream(self, *args, **kwargs):
        """Monitor a stream"""
        return self.monitor.monitor(*args, **kwargs)

    def monitor_forget(self, stream):
        """Forget monitoring a stream"""
        return self.monitor.forget(stream)

    def _extract_exception(self, result):
        key = 'exception'
        return key if key in result and result[key] != None else None

    def _combine_results(self):
        results = []
        for result_set_key in self.result_sets:
            result_set = self.result_sets[result_set_key]
            for result_key in result_set:
                result = result_set[result_key]
                exception = self._extract_exception(result)
                code_string = result['code'] if 'code' in result else None
                code = int(code_string) if code_string else 0
                name = result['name']
                status = exception if exception else code if name != 'fail' else not code
                if status != 0:
                    results.append('%02d:%s:%s' % (result_set_key, name, status))
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
