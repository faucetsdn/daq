"""DHCP server module for device testing"""

import os

from clib import docker_host
from clib import tcpdump_helper

import dhcp_monitor
import logger

LOGGER = logger.get_logger('dhcp_server')


class DHCPServer():
    """DHCP server class"""

    def __init__(self, runner, host_port, tmpdir, dhcp_callback):
        self.runner = runner
        assert host_port > 0, 'host_port %d, must be > 0' % host_port
        self._host_port = host_port
        self._tmpdir = tmpdir
        self._dhcp_callback = dhcp_callback
        self.dhcp_monitor = None
        self.host = None
        self._host_intf = None
        self._scan_monitor = None

    def __repr__(self):
        return 'DHCP server on port %d' % self._host_port

    def initialize(self):
        """Initialize the DHCP server"""
        try:
            self._initialize()
        except Exception as e:
            LOGGER.error(
                'DHCP server initialization failed, terminating: %s', str(e))
            self.terminate()
            raise

    def _initialize(self):
        LOGGER.info('Initializing DHCP server on port %d', self._host_port)
        cls = docker_host.make_docker_host(
            'daqf/networking', prefix='daq', network='bridge')
        # Work around an instability in the faucet/clib/docker library, b/152520627.
        if getattr(cls, 'pullImage'):
            setattr(cls, 'pullImage', lambda x: True)
        host_name = 'dhcp%02d' % self._host_port
        host = self.runner.add_host(
            host_name, port=self._host_port, cls=cls, tmpdir=self._tmpdir)
        host.activate()
        self.host = host
        self._change_lease_time(
            self.runner.config.get('initial_dhcp_lease_time'))
        LOGGER.info("Added networking host on port %d at %s",
                    self._host_port, host.IP())
        self._host_intf = self.runner.get_host_interface(host)
        self._startup_scan(host)
        log_file = os.path.join(self._tmpdir, 'dhcp_monitor.txt')
        self.dhcp_monitor = dhcp_monitor.DhcpMonitor(self.runner, host,
                                                     self._dhcp_callback, log_file)
        self.dhcp_monitor.start()

    def activate(self):
        """Won't be necessary when DHCP lease time test is moved."""
        self._change_lease_time(self.runner.config.get("dhcp_lease_time"))
        self._scan_finalize()

    def _change_lease_time(self, lease_time):
        LOGGER.info('%s change lease time to %s', repr(self), lease_time)
        self.execute_script('change_lease_time', lease_time)

    def _scan_finalize(self, forget=True):
        if self._scan_monitor:
            active = self._scan_monitor.stream() and not self._scan_monitor.stream().closed
            assert active == forget, 'forget and active mismatch'
            if forget:
                self.runner.monitor_forget(self._scan_monitor.stream())
                self._scan_monitor.terminate()
            self._scan_monitor = None

    def execute_script(self, action, *args):
        """Generic function for executing scripts"""
        self.host.cmd(('./%s' + len(args) * ' %s') % (action, *args))

    def request_new_ip(self, mac):
        """Requests a new ip for the device"""
        self.execute_script('new_ip', mac)

    def change_dhcp_response_time(self, mac, time):
        """Change dhcp response time for device mac"""
        self.execute_script('change_dhcp_response_time', mac, time)

    def _startup_scan(self, host):
        assert not self._scan_monitor, 'startup_scan already active'
        startup_file = '/tmp/dhcp_server.pcap'
        LOGGER.info('%s startup capture %s in container\'s %s', repr(self),
                    self._host_intf, startup_file)
        tcp_filter = ''
        helper = tcpdump_helper.TcpdumpHelper(host, tcp_filter, packets=None,
                                              intf_name=self._host_intf, timeout=None,
                                              pcap_out=startup_file, blocking=False)
        self._scan_monitor = helper
        self.runner.monitor_stream('start%d' % self._host_port, helper.stream(),
                                   helper.next_line, hangup=self._scan_complete,
                                   error=self._scan_error)

    def _scan_complete(self):
        LOGGER.info('%s scan complete', repr(self))
        self._scan_finalize(forget=False)

    def _scan_error(self, e):
        LOGGER.error('%s monitor error: %s', repr(self), e)
        self._scan_finalize()

    def terminate(self):
        """Terminate this instance"""
        LOGGER.info('Terminating %s', repr(self))
        if self.dhcp_monitor:
            self.dhcp_monitor.cleanup()
        self._scan_finalize()
        if self.host:
            try:
                self.host.terminate()
                self.runner.remove_host(self.host)
                self.host = None
            except Exception as e:
                LOGGER.error(
                    '%s terminate failure: %s', repr(self), e)
                LOGGER.exception(e)
