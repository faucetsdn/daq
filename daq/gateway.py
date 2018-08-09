"""Gateway module for device testing"""

import logging
import os
import shutil

from clib import docker_host

import dhcp_monitor

LOGGER = logging.getLogger('gateway')

class Gateway(object):
    """Gateway collection class for managing testing services"""

    HOST_OFFSET = 0
    DUMMY_OFFSET = 1
    TEST_OFFSET = 2
    SET_SPACING = 10

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

    def initialize(self):
        """Initialize the gateway host"""
        host_name = 'gw%02d' % self.port_set
        host_port = self._switch_port(self.HOST_OFFSET)
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

        self.dhcp_monitor = dhcp_monitor.DhcpMonitor(self.runner, host, self._dhcp_callback)
        self.dhcp_monitor.start()

        assert self._ping_test(host, dummy), 'ping failed'
        assert self._ping_test(dummy, host), 'ping failed'
        assert self._ping_test(dummy, self.fake_target), 'ping failed'
        assert self._ping_test(host, dummy, src_addr=self.fake_target), 'ping failed'

        self.host = host

    def get_test_port(self):
        """Get the test port to use for this gateway setup"""
        return self._switch_port(self.TEST_OFFSET)

    def _switch_port(self, offset):
        return self.port_set * self.SET_SPACING + offset

    def _dhcp_callback(self, state, target_ip=None, target_mac=None, exception=None):
        self.runner.dhcp_notify(state, target_ip=target_ip,
                                target_mac=target_mac, exception=exception)

    def _setup_tmpdir(self, base_name):
        tmpdir = os.path.join('inst', base_name)
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.makedirs(tmpdir)
        return tmpdir

    def terminate(self):
        """Terminate this instance"""
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
