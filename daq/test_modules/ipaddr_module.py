"""Test module encapsulating ip-address tests (including DHCP)"""

from __future__ import absolute_import

import time
from datetime import datetime, timedelta
import copy

from proto.system_config_pb2 import DhcpMode
import host as connected_host
from .docker_module import DockerModule
from .base_module import HostModule


LEASE_TIME_UNITS_CONVERTER = {
    's': 1,
    'm': 60,
    'h': 60 ** 2,
    'd': 24 * 60 ** 2
}


class IpAddrModule(HostModule):
    """Module for inline ipaddr tests"""
    _TIMEOUT_EXCEPTION = TimeoutError('DHCP analysis step timeout expired')

    def __init__(self, host, tmpdir, test_name, module_config):
        super().__init__(host, tmpdir, test_name, module_config)
        self.docker_host = DockerModule(host, tmpdir, test_name, module_config)
        self.test_dhcp_ranges = copy.copy(self.test_config.get('dhcp_ranges', []))
        self._ip_callback = None
        self._lease_time_seconds = self._get_lease_time()
        self.tests = [
            ('dhcp port_toggle test', self._dhcp_port_toggle_test),
            ('dhcp multi subnet test', self._multi_subnet_test),
            ('ip change test', self._ip_change_test),
            ('dhcp change test', self._dhcp_change_test),
            ('analyze results', self._analyze)
        ]
        self._logger = self.get_logger('ipaddr')
        self._force_terminated = False
        self._timeout = None

    def start(self, port, params, callback, finish_hook):
        """Start the ip-addr tests"""
        super().start(port, params, callback, finish_hook)
        assert self.host.device.dhcp_mode != DhcpMode.EXTERNAL, "device DHCP is not enabled."
        self._logger.info('Target device %s starting ipaddr test %s', self.device, self.test_name)
        # Wait for initial ip before beginning test.
        self._ip_callback = self._next_test

    def _get_lease_time(self):
        lease_time = self.host.config.get("dhcp_lease_time")
        if not lease_time or lease_time[-1] not in LEASE_TIME_UNITS_CONVERTER:
            return None
        return float(lease_time[:-1]) * LEASE_TIME_UNITS_CONVERTER[lease_time[-1]]

    def _set_timeout(self):
        if not self._lease_time_seconds:
            return
        self._timeout = datetime.now() + timedelta(seconds=self._lease_time_seconds)
        self._logger.info('Device %s setting dhcp timeout at %s', self.device, self._timeout)

    def _next_test(self):
        try:
            self._timeout = None
            name, func = self.tests.pop(0)
            self._logger.info('Device %s running %s', self.device, name)
            func()
        except Exception as e:
            self._logger.error('Exception for %s: %s', self.device, str(e))
            self._finalize(exception=e)

    def _dhcp_port_toggle_test(self):
        self._set_timeout()
        if not self.host.connect_port(False):
            self._logger.error('Disconnect port not enabled %s', self.device)
            return
        time.sleep(self.host.config.get("port_debounce_sec", 0) + 1)
        self.host.connect_port(True)
        self._ip_callback = self._next_test

    def _multi_subnet_test(self):
        self._set_timeout()
        if not self.test_dhcp_ranges:
            self._next_test()
            return
        dhcp_range = self.test_dhcp_ranges.pop(0)
        self._logger.info('Testing %s dhcp range: %s', self.device, str(dhcp_range))
        args = (dhcp_range["start"], dhcp_range["end"], dhcp_range["prefix_length"])
        self.host.gateway.change_dhcp_range(*args)
        self._ip_callback = self._multi_subnet_test if self.test_dhcp_ranges else self._next_test

    def _ip_change_test(self):
        self._set_timeout()
        self.host.gateway.request_new_ip(self.host.target_mac)
        self._ip_callback = self._next_test

    def _dhcp_change_test(self):
        self._set_timeout()
        if not self.host.connect_port(False):
            self._logger.error('Disconnect port not enabled %s', self.device)
            return
        self.host.gateway.request_new_ip(self.host.target_mac)
        self.host.connect_port(True)
        self._ip_callback = self._next_test

    def _analyze(self):
        self._set_timeout()
        self._ip_callback = None
        self.docker_host.start(self.port, self.params,
                               self._finalize, self._finish_hook)

    def _finalize(self, return_code=None, exception=None):
        self._logger.debug('Module finalizing')
        self._ip_callback = None
        if not self._force_terminated:
            self.callback(return_code=return_code, exception=exception)

    def terminate(self):
        """Terminate this set of tests"""
        self._logger.debug('Module terminating')
        self._force_terminated = True
        if self.docker_host.start_time:
            self.docker_host.terminate()
        self._finalize()

    def ip_listener(self, target_ip, state):
        """Respond to a ip notification event"""
        self._logger.info('Device %s ip notification %s (%s)', self.device, target_ip, state)
        if state not in (connected_host.MODE.DONE, connected_host.MODE.LONG):
            return
        result = self.host.runner.ping_test(self.host.gateway.host, self.host.target_ip)
        self._logger.info('Ping to %s, result %s', self.host.target_ip, result)
        if self._ip_callback:
            self._ip_callback()

    def heartbeat(self):
        if self._timeout and datetime.now() >= self._timeout:
            if self.docker_host.start_time:
                self.terminate()
                self.callback(exception=self._TIMEOUT_EXCEPTION)
            else:
                self._logger.error('Device %s dhcp timeout after %ds lease time',
                                   self.device, self._lease_time_seconds)
                self.tests = self.tests[-1:]
                self._next_test()
