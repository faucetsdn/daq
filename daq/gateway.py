"""Gateway module for device testing"""

import datetime
import logging
import os
import shutil

from clib import docker_host

import dhcp_monitor

LOGGER = logging.getLogger('gateway')

class Gateway():
    """Gateway collection class for managing testing services"""

    HOST_OFFSET = 0
    DUMMY_OFFSET = 1
    TEST_OFFSET_START = 2
    TEST_OFFSET_LIMIT = 10
    SET_SPACING = 10
    _PING_RETRY_COUNT = 10

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
        self.test_ports = {}
        self.ready = {}
        self.activated = False

    def initialize(self):
        """Initialize the gateway host"""
        try:
            self._initialize()
        except:
            self.terminate()
            raise

    def _initialize(self):
        host_name = 'gw%02d' % self.port_set
        host_port = self._switch_port(self.HOST_OFFSET)
        LOGGER.info('Initializing gateway %s as %s/%d', self.name, host_name, host_port)
        self.tmpdir = self._setup_tmpdir(host_name)
        cls = docker_host.make_docker_host('daq/networking', prefix='daq', network='bridge')
        host = self.runner.add_host(host_name, port=host_port, cls=cls, tmpdir=self.tmpdir)
        host.activate()
        LOGGER.info("Adding networking host %s on port %d at %s", host_name, host_port, host.IP())

        dummy_name = 'dummy%02d' % self.port_set
        dummy_port = self._switch_port(self.DUMMY_OFFSET)
        self.dummy = self.runner.add_host(dummy_name, port=dummy_port)
        dummy = self.dummy
        LOGGER.info("Added dummy target %s on port %d at %s", dummy_name, dummy_port, dummy.IP())

        self.fake_target = self.TEST_IP_FORMAT % self.port_set
        LOGGER.debug('Adding fake target at %s', self.fake_target)
        intf = self.runner.get_host_interface(host)
        host.cmd('ip addr add %s dev %s' % (self.fake_target, intf))

        # Dummy doesn't use DHCP, so need to set default route manually.
        dummy.cmd('route add -net 0.0.0.0 gw %s' % host.IP())

        log_file = os.path.join(self.tmpdir, 'dhcp_monitor.txt')
        self.dhcp_monitor = dhcp_monitor.DhcpMonitor(self.runner, host,
                                                     self._dhcp_callback, log_file)
        self.dhcp_monitor.start()

        ping_retry = self._PING_RETRY_COUNT
        while not self._ping_test(host, dummy) and ping_retry:
            ping_retry -= 1
            LOGGER.info('Gateway %s warmup ping failed at %s', host_name, datetime.datetime.now())

        assert self._ping_test(host, dummy), 'dummy ping failed'
        assert self._ping_test(dummy, host), 'host ping failed'
        assert self._ping_test(dummy, self.fake_target), 'fake ping failed'
        assert self._ping_test(host, dummy, src_addr=self.fake_target), 'reverse ping failed'

        self.host = host

    def allocate_test_port(self):
        """Get the test port to use for this gateway setup"""
        test_port = self._switch_port(self.TEST_OFFSET_START)
        while test_port in self.test_ports:
            test_port = test_port + 1
        limit_port = self._switch_port(self.TEST_OFFSET_LIMIT)
        assert test_port < limit_port, 'no test ports available'
        self.test_ports[test_port] = True
        return test_port

    def release_test_port(self, test_port):
        """Release the given port from the gateway"""
        assert test_port in self.test_ports, 'test port not allocated'
        del self.test_ports[test_port]

    def get_port_range(self):
        """Get the port range utilized by this gateway group"""
        return (self._switch_port(0), self._switch_port(self.SET_SPACING))

    def _switch_port(self, offset):
        return self.port_set * self.SET_SPACING + offset

    def _is_target_expected(self, target):
        target_mac = target['mac']
        for target_port in self.targets:
            if self.targets[target_port]['mac'] == target_mac:
                return True
        LOGGER.warning('No target match found for %s in %s', target_mac, self.name)
        return False

    def _dhcp_callback(self, state, target_ip=None, target_mac=None, exception=None):
        target = {
            'ip': target_ip,
            'mac': target_mac
        }
        if self._is_target_expected(target) and not exception:
            self.runner.dhcp_notify(state, target=target, gateway_set=self.port_set)
        else:
            LOGGER.warning('Unexpected target %s for gateway %s', target_mac, self.name)

    def _setup_tmpdir(self, base_name):
        tmpdir = os.path.join('inst', base_name)
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.makedirs(tmpdir)
        return tmpdir

    def attach_target(self, target_port, target):
        """Attach the given target to this gateway; return number of attached targets."""
        assert target_port not in self.targets, 'target already attached to gw'
        LOGGER.info('Attaching target %d to gateway group %s', target_port, self.name)
        self.targets[target_port] = target
        return len(self.targets)

    def detach_target(self, target_port):
        """Detach the given target from this gateway; return number of remaining targets."""
        assert target_port in self.targets, 'target not attached to gw'
        LOGGER.info('Detach target %d from gateway group %s', target_port, self.name)
        del self.targets[target_port]
        return len(self.targets)

    def target_ready(self, target_mac):
        """Mark a target ready, and return set of ready targets"""
        if not target_mac in self.ready:
            LOGGER.info('Ready target %s from gateway group %s', target_mac, self.name)
            self.ready[target_mac] = True
        return self.ready

    def get_targets(self):
        """Return the host targets associated with this gateway"""
        return self.targets.values()

    def terminate(self):
        """Terminate this instance"""
        assert not self.targets, 'gw %s has targets %s' % (self.name, self.targets)
        LOGGER.info('Terminating gateway %s', self.name)
        if self.dhcp_monitor:
            self.dhcp_monitor.cleanup()
        if self.host:
            try:
                self.host.terminate()
                self.runner.remove_host(self.host)
                self.host = None
            except Exception as e:
                LOGGER.error('Gateway %s terminating host: %s', self.name, e)
                LOGGER.exception(e)
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
