"""Main test runner for DAQ"""

import logging
import os
import time

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, Host
from mininet.link import Intf
from mininet.cli import CLI

from clib.mininet_test_topo import FaucetHostCleanup

from faucet_event_client import FaucetEventClient
from stream_monitor import StreamMonitor
from host import ConnectedHost

from gcp import GcpManager

LOGGER = logging.getLogger('runner')


class DAQHost(FaucetHostCleanup, Host):
    """Base Mininet Host class, for Mininet-based tests."""
    #pylint: disable=too-few-public-methods
    pass


class DummyNode(object):
    """Dummy node used to handle shadow devices"""
    #pylint: disable=invalid-name
    def addIntf(self, node, port=None):
        """No-op for adding an interface"""
        pass

    def cmd(self, cmd, *args, **kwargs):
        """No-op for running a command"""
        pass


class DAQRunner(object):
    """Main runner class controlling DAQ. Primarily mediates between
    faucet events, connected hosts (to test), and gcp for logging. This
    class owns the main event loop and shards out work to subclasses."""

    config = None
    net = None
    device_intfs = None
    target_sets = None
    active_ports = None
    result_sets = None
    pri = None
    sec = None
    sec_dpid = None
    sec_port = None
    sec_name = None
    gcp = None
    description = None
    version = None
    faucet_events = None
    flap_ports = None
    event_start = None
    monitor = None
    one_shot = None
    exception = None
    switch_links = None

    def __init__(self, config):
        self.config = config
        self.target_sets = {}
        self.result_sets = {}
        self.active_ports = {}
        self.switch_links = {}
        self.gcp = GcpManager(self.config)
        raw_description = config.get('site_description', '')
        self.description = raw_description.strip("\"")
        self.version = os.environ['DAQ_VERSION']

    #pylint: disable=too-many-arguments
    def add_host(self, name, cls=DAQHost, ip_addr=None, env_vars=None, vol_maps=None,
                 port=None, tmpdir=None):
        """Add a host to the ecosystem"""
        params = {'ip': ip_addr} if ip_addr else {}
        params['tmpdir'] = os.path.join(tmpdir, 'nodes') if tmpdir else None
        params['env_vars'] = env_vars if env_vars else []
        params['vol_maps'] = vol_maps if vol_maps else []
        host = self.net.addHost(name, cls, **params)
        try:
            LOGGER.debug('Created host %s with pid %s/%s', name, host.pid, host.shell.pid)
            switch_link = self.net.addLink(self.pri, host, port1=port, fast=False)
            self.switch_links[host] = switch_link
            if self.net.built:
                host.configDefault()
                self._switch_attach(self.pri, switch_link.intf1)
        except:
            host.terminate()
            raise
        return host

    def get_host_interface(self, host):
        """Get the internal link interface for this host"""
        return self.switch_links[host].intf2

    def _switch_attach(self, switch, intf):
        switch.attach(intf)
        # This really should be done in attach, but currently only automatic on switch startup.
        switch.vsctl(switch.intfOpts(intf))

    def _switch_del_intf(self, switch, intf):
        del switch.intfs[switch.ports[intf]]
        del switch.ports[intf]
        del switch.nameToIntf[intf.name]

    def remove_host(self, host):
        """Remove a host from the ecosystem"""
        index = self.net.hosts.index(host)
        if index:
            del self.net.hosts[index]
        if host in self.switch_links:
            switch_link = self.switch_links[host]
            del self.switch_links[host]
            intf = switch_link.intf1
            self.pri.detach(intf)
            self._switch_del_intf(self.pri, intf)
            intf.delete()
            del self.net.links[self.net.links.index(switch_link)]

    def _make_device_intfs(self):
        intf_names = self.config['daq_intf'].split(',')
        intfs = []
        for intf_name in intf_names:
            intf_name = intf_name[0:-1] if intf_name.endswith('!') else intf_name
            port_no = len(intfs) + 1
            intf = Intf(intf_name.strip(), node=DummyNode(), port=port_no)
            intf.port = port_no
            intfs.append(intf)
        return intfs

    def _flush_faucet_events(self):
        LOGGER.info('Flushing faucet event queue...')
        while self.faucet_events.next_event():
            pass

    def _flap_interface_ports(self):
        if self.device_intfs:
            for device_intf in self.device_intfs:
                self._flap_interface_port(device_intf.name)

    def _flap_interface_port(self, intf_name):
        if intf_name.startswith('faux') or intf_name == 'local':
            LOGGER.info('Flapping device interface %s.', intf_name)
            self.sec.cmd('ip link set %s down' % intf_name)
            time.sleep(0.5)
            self.sec.cmd('ip link set %s up' % intf_name)

    def _create_secondary(self):
        self.sec_port = int(self.config['ext_port'] if 'ext_port' in self.config else 47)
        if 'ext_dpid' in self.config:
            self.sec_dpid = int(self.config['ext_dpid'], 0)
            self.sec_name = self.config['ext_intf']
            LOGGER.info('Configuring external secondary with dpid %s on intf %s',
                        self.sec_dpid, self.sec_name)
            sec_intf = Intf(self.sec_name, node=DummyNode(), port=1)
            self.pri.addIntf(sec_intf, port=1)
        else:
            self.sec_dpid = 2
            LOGGER.info('Creating ovs secondary with dpid/port %s/%d',
                        self.sec_dpid, self.sec_port)
            self.sec = self.net.addSwitch('sec', dpid=str(self.sec_dpid), cls=OVSSwitch)

            link = self.net.addLink(self.pri, self.sec, port1=1,
                                    port2=self.sec_port, fast=False)
            LOGGER.info('Added switch link %s <-> %s', link.intf1.name, link.intf2.name)
            self.sec_name = link.intf2.name

    def _send_heartbeat(self):
        self.gcp.publish_message('daq_runner', {
            'name': 'status',
            'tests': ConnectedHost.TEST_ORDER,
            'ports': self.active_ports.keys(),
            'description': self.description,
            'version': self.version,
            'timestamp': int(time.time()),
        })

    def initialize(self):
        """Initialize DAQ instance"""
        self._send_heartbeat()

        LOGGER.debug("Creating miniet...")
        self.net = Mininet()

        LOGGER.debug("Adding switches...")
        self.pri = self.net.addSwitch('pri', dpid='1', cls=OVSSwitch)

        LOGGER.info("Starting faucet...")
        output = self.pri.cmd('cmd/faucet && echo SUCCESS')
        if not output.strip().endswith('SUCCESS'):
            LOGGER.info('Faucet output: %s', output)
            assert False, 'Faucet startup failed'

        self._create_secondary()

        target_ip = "127.0.0.1"
        LOGGER.debug("Adding controller at %s", target_ip)
        self.net.addController('controller', controller=RemoteController,
                               ip=target_ip, port=6633)

        LOGGER.info("Starting mininet...")
        self.net.start()

        if self.sec:
            self.device_intfs = self._make_device_intfs()
            for device_intf in self.device_intfs:
                LOGGER.info("Attaching device interface %s on port %d.",
                            device_intf.name, device_intf.port)
                self.sec.addIntf(device_intf, port=device_intf.port)
                self._switch_attach(self.sec, device_intf)

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
            self.pri.cmd('docker kill daq-faucet')
        except Exception as e:
            LOGGER.error('Exception: %s', e)
        try:
            LOGGER.debug("Stopping mininet...")
            self.net.stop()
        except Exception as e:
            LOGGER.error('Exception: %s', e)
        LOGGER.info("Done with runner.")

    def _handle_faucet_event(self):
        target_dpid = int(self.sec_dpid)
        while True:
            event = self.faucet_events.next_event()
            LOGGER.debug('Faucet event %s', event)
            if not event:
                break
            (dpid, port, active) = self.faucet_events.as_port_state(event)
            LOGGER.debug('Port state is dpid %s port %s active %s', dpid, port, active)
            if dpid == target_dpid:
                if active:
                    if port >= self.sec_port:
                        LOGGER.debug('Ignoring out-of-range port %d', port)
                    else:
                        self.active_ports[port] = True
                        self._trigger_target_set(port)
                else:
                    if port in self.active_ports:
                        del self.active_ports[port]
                    self._cancel_target_set(port)

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

        if self.flap_ports:
            self._flap_interface_ports()

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

        if not self.one_shot and not self.exception:
            LOGGER.info('Dropping into interactive command line')
            CLI(self.net)

        self._terminate()

    def _trigger_target_set(self, port_set):
        assert port_set not in self.target_sets, 'target set %d already exists' % port_set
        try:
            LOGGER.debug('Trigger target set %d', port_set)
            self.target_sets[port_set] = ConnectedHost(self, port_set)
            self._send_heartbeat()
        except Exception as e:
            self.target_set_error(port_set, e)

    def target_set_error(self, port_set, e):
        """Handle an error in the target port set"""
        LOGGER.info('Set %d exception: %s', port_set, e)
        LOGGER.exception(e)
        if port_set in self.target_sets:
            target_set = self.target_sets[port_set]
            target_set.record_result(target_set.test_name, exception=e)
            target_set.terminate(trigger=False)
            self.target_set_complete(target_set)
        else:
            self._target_set_finalize(port_set, {'exception': str(e)})

    def target_set_complete(self, target_set):
        """Handle completion of a target_set"""
        port_set = target_set.port_set
        results = target_set.results
        self._cancel_target_set(port_set)
        self._target_set_finalize(port_set, results)

    def _target_set_finalize(self, port_set, results):
        LOGGER.info('Set %d complete, %d results', port_set, len(results))
        self.result_sets[port_set] = results
        LOGGER.info('Remaining sets: %s', self.target_sets.keys())

    def _cancel_target_set(self, port_set):
        if port_set in self.target_sets:
            target_set = self.target_sets[port_set]
            del self.target_sets[port_set]
            target_set.terminate(trigger=False)
            LOGGER.info('Set %d cancelled.', port_set)
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
                code = int(result['code']) if 'code' in result else 0
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
