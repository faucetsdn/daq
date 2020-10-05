"""Gateway module for device testing"""

import os

from clib import docker_host
from clib import tcpdump_helper

import dhcp_monitor
import logger
from base_gateway import BaseGateway

LOGGER = logger.get_logger('gateway')


class ContainerGateway(BaseGateway):
    """Gateway collection class for managing testing services"""

    def __init__(self, *args):
        super().__init__(*args)
        self._scan_monitor = None
        self.dhcp_monitor = None

    def _initialize(self):
        super()._initialize()
        self._change_lease_time(
            self.runner.config.get('initial_dhcp_lease_time'))
        self._startup_scan(self.host)
        log_file = os.path.join(self.tmpdir, 'dhcp_monitor.txt')
        self.dhcp_monitor = dhcp_monitor.DhcpMonitor(self.runner, self.host,
                                                     self._dhcp_callback, log_file=log_file)
        self.dhcp_monitor.start()

    def _get_host_class(self):
        cls = docker_host.make_docker_host(
            'daqf/networking', prefix='daq', network='bridge')
        # Work around an instability in the faucet/clib/docker library, b/152520627.
        if getattr(cls, 'pullImage'):
            setattr(cls, 'pullImage', lambda x: True)
        return cls

    def activate(self):
        """Mark this gateway as activated once all hosts are present"""
        super().activate()
        self._change_lease_time(self.runner.config.get("dhcp_lease_time"))
        self._scan_finalize()

    def _change_lease_time(self, lease_time):
        LOGGER.info('Gateway %s change lease time to %s', self.port_set, lease_time)
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
        """Generic function for executing scripts on gateway"""
        self.host.cmd(('./%s' + len(args) * ' %s') % (action, *args))

    def request_new_ip(self, mac):
        """Requests a new ip for the device"""
        self.execute_script('new_ip', mac)

    def change_dhcp_response_time(self, mac, time):
        """Change dhcp response time for device mac"""
        self.execute_script('change_dhcp_response_time', mac, time)

    def stop_dhcp_response(self, mac):
        """Stops DHCP response for the device"""
        self.change_dhcp_response_time(mac, -1)

    def change_dhcp_range(self, start, end, prefix_length):
        """Change dhcp range for devices"""
        self.execute_script('change_dhcp_range', start, end, prefix_length)

    def _startup_scan(self, host):
        assert not self._scan_monitor, 'startup_scan already active'
        startup_file = '/tmp/gateway.pcap'
        LOGGER.info('Gateway %s startup capture %s in container\'s %s', self.port_set,
                    self.host_intf, startup_file)
        tcp_filter = ''
        helper = tcpdump_helper.TcpdumpHelper(host, tcp_filter, packets=None,
                                              intf_name=self.host_intf, timeout=None,
                                              pcap_out=startup_file, blocking=False)
        self._scan_monitor = helper
        self.runner.monitor_stream('start%d' % self.port_set, helper.stream(),
                                   helper.next_line, hangup=self._scan_complete,
                                   error=self._scan_error)

    def _scan_complete(self):
        LOGGER.info('Gateway %d scan complete', self.port_set)
        self._scan_finalize(forget=False)

    def _scan_error(self, e):
        LOGGER.error('Gateway %d monitor error: %s', self.port_set, e)
        self._scan_finalize()

    def terminate(self):
        """Terminate this instance"""
        super().terminate()
        self._scan_finalize()
