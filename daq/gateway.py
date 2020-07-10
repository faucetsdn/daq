"""Gateway module for device testing"""

import datetime
import os
import shutil
from dhcp_server import DHCPServer
import logger

LOGGER = logger.get_logger('gateway')


class Gateway():
    """Gateway collection class for managing testing services"""

    GATEWAY_OFFSET = 0
    DUMMY_OFFSET = 1
    TEST_OFFSET_START = 2
    NUM_SET_PORTS = 6
    SET_SPACING = 10
    _PING_RETRY_COUNT = 5

    TEST_IP_FORMAT = '192.168.84.%d'

    def __init__(self, runner, name, port_set, network):
        self.name = name
        self.runner = runner
        assert port_set > 0, 'port_set %d, must be > 0' % port_set
        self.port_set = port_set
        self.network = network
        self.dhcp_monitor = None
        self.fake_target = None
        self.host = None
        self.dummy = None
        self.tmpdir = None
        self.targets = {}
        self.test_ports = set()
        self.ready = set()
        self.activated = False
        self.result_linger = False
        self._dhcp_servers = {}

    def initialize(self):
        """Initialize the gateway host"""
        try:
            self._initialize()
        except Exception as e:
            LOGGER.error(
                'Gateway initialization failed, terminating: %s', str(e))
            self.terminate()
            raise

    def _initialize(self):
        host_name = 'gw%02d' % self.port_set
        host_port = self._switch_port(self.GATEWAY_OFFSET)
        LOGGER.info('Initializing gateway %s as %s/%d',
                    self.name, host_name, host_port)
        self.tmpdir = self._setup_tmpdir('inst', host_name)
        self.host = self._start_dhcp_server(host_port).host

        dummy_name = 'dummy%02d' % self.port_set
        dummy_port = self._switch_port(self.DUMMY_OFFSET)
        dummy = self.runner.add_host(dummy_name, port=dummy_port)
        # Dummy does not use DHCP, so need to set default route manually.
        dummy.cmd('route add -net 0.0.0.0 gw %s' % self.host.IP())
        self.dummy = dummy
        LOGGER.info("Added dummy target %s on port %d at %s",
                    dummy_name, dummy_port, dummy.IP())

        self.fake_target = self.TEST_IP_FORMAT % self.port_set
        host_intf = self.runner.get_host_interface(self.host)
        LOGGER.debug('Adding fake target at %s to %s',
                     self.fake_target, host_intf)
        self.host.cmd('ip addr add %s dev %s' %
                      (self.fake_target, host_intf))

        ping_retry = self._PING_RETRY_COUNT
        while not self._ping_test(self.host, dummy):
            ping_retry -= 1
            LOGGER.info('Gateway %s warmup failed at %s with %d',
                        host_name, datetime.datetime.now(), ping_retry)
            assert ping_retry, 'warmup ping failure'

        assert self._ping_test(self.host, dummy), 'dummy ping failed'
        assert self._ping_test(dummy, self.host), 'host ping failed'
        assert self._ping_test(dummy, self.fake_target), 'fake ping failed'
        assert self._ping_test(
            self.host, dummy, src_addr=self.fake_target), 'reverse ping failed'

    def _start_dhcp_server(self, host_port) -> DHCPServer:
        tmpdir = self._setup_tmpdir(self.tmpdir, 'dhcp%02d' % host_port)
        dhcp_server = DHCPServer(
            self.runner, host_port, tmpdir, self._dhcp_callback)
        dhcp_server.initialize()
        self._dhcp_servers[host_port] = dhcp_server
        return dhcp_server

    def activate(self):
        """Mark this gateway as activated once all hosts are present"""
        for _, dhcp_server in self._dhcp_servers.items():
            dhcp_server.activate()
        self.activated = True

    def request_new_ip(self, mac):
        """Requests a new ip for the device"""
        for _, dhcp_server in self._dhcp_servers.items():
            dhcp_server.request_new_ip(mac)

    def change_dhcp_response_time(self, mac, time):
        """Changes DHCP response time for the device"""
        for _, dhcp_server in self._dhcp_servers.items():
            dhcp_server.change_dhcp_response_time(mac, time)

    def stop_dhcp_response(self, mac):
        """Stops DHCP respopnse for the device"""
        self.change_dhcp_response_time(mac, -1)

    def allocate_test_port(self):
        """Get the test port to use for this gateway setup"""
        test_port = self._switch_port(self.TEST_OFFSET_START)
        while test_port in self.test_ports:
            test_port = test_port + 1
        limit_port = self._switch_port(self.NUM_SET_PORTS)
        assert test_port < limit_port, 'no test ports available'
        self.test_ports.add(test_port)
        return test_port

    def release_test_port(self, test_port):
        """Release the given port from the gateway"""
        assert test_port in self.test_ports, 'test port not allocated'
        self.test_ports.remove(test_port)

    def _switch_port(self, offset):
        return self.port_set * self.SET_SPACING + offset

    def _is_target_expected(self, target):
        if not target:
            return False
        target_mac = target['mac']
        for target_port in self.targets:
            if self.targets[target_port]['mac'] == target_mac:
                return True
        LOGGER.warning('No target match found for %s in %s',
                       target_mac, self.name)
        return False

    def _dhcp_callback(self, state, target, exception=None):
        if exception:
            LOGGER.error('Gateway DHCP exception %s', exception)
        if self._is_target_expected(target) or exception:
            self.runner.ip_notify(
                state, target, self.port_set, exception=exception)

    def _setup_tmpdir(self, *folders):
        tmpdir = os.path.join(*folders)
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.makedirs(tmpdir)
        return tmpdir

    def attach_target(self, target_port, target):
        """Attach the given target to this gateway; return number of attached targets."""
        assert target_port not in self.targets, 'target already attached to gw'
        LOGGER.info('Attaching target %d to gateway group %s',
                    target_port, self.name)
        self.targets[target_port] = target
        return len(self.targets)

    def detach_target(self, target_port):
        """Detach the given target from this gateway; return number of remaining targets."""
        assert target_port in self.targets, 'target not attached to gw'
        LOGGER.info('Detach target %d from gateway group %s: %s',
                    target_port, self.name, list(self.targets.keys()))
        del self.targets[target_port]
        return len(self.targets)

    def target_ready(self, target_mac):
        """Mark a target ready, and return set of ready targets"""
        if not target_mac in self.ready:
            LOGGER.info('Ready target %s from gateway group %s',
                        target_mac, self.name)
            self.ready.add(target_mac)
        return self.ready

    def get_targets(self):
        """Return the host targets associated with this gateway"""
        return self.targets.values()

    def terminate(self):
        """Terminate this instance"""
        assert not self.targets, 'gw %s has targets %s' % (
            self.name, self.targets)
        LOGGER.info('Terminating gateway %d/%s', self.port_set, self.name)
        for _, dhcp_server in self._dhcp_servers.items():
            try:
                dhcp_server.terminate()
            except Exception as e:
                LOGGER.error('Gateway %s terminating host: %s', self.name, e)
                LOGGER.exception(e)
        self.host = None
        if self.dummy:
            try:
                self.dummy.terminate()
                self.runner.remove_host(self.dummy)
                self.dummy = None
            except Exception as e:
                LOGGER.error('Gateway %s terminating dummy: %s', self.name, e)
                LOGGER.exception(e)

    def _ping_test(self, src, dst, src_addr=None):
        return self.runner.ping_test(src, dst, src_addr=src_addr)
