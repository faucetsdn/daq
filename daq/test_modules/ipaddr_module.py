"""Test module encapsulating ip-address tests (including DHCP)"""

from __future__ import absolute_import
import logging

import time
from datetime import datetime, timedelta
import os
import copy
import logger
from .docker_module import DockerModule
from .base_module import HostModule
from proto.system_config_pb2 import DhcpMode

_LOG_FORMAT = "%(asctime)s %(levelname)-7s %(message)s"
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
        self._logger = logger.get_logger('ipaddr_%s' % self.host_name)
        log_folder = os.path.join(self.tmpdir, 'nodes', self.host_name, 'tmp')
        os.makedirs(log_folder)
        log_path = os.path.join(log_folder, 'activate.log')
        self._file_handler = logging.FileHandler(log_path)
        formatter = logging.Formatter(_LOG_FORMAT)
        self._file_handler.setFormatter(formatter)
        self._logger.addHandler(self._file_handler)
        self._force_terminated = False
        self._timeout = None

    def start(self, port, params, callback, finish_hook):
        """Start the ip-addr tests"""
        super().start(port, params, callback, finish_hook)
        assert self.host.device.dhcp_mode != DhcpMode.EXTERNAL, "device DHCP is not enabled."
        self._logger.debug('Target device %s starting ipaddr test %s', self.device, self.test_name)
        self._next_test()

    def _get_lease_time(self):
        lease_time = self.host.config.get("dhcp_lease_time")
        if not lease_time or lease_time[-1] not in LEASE_TIME_UNITS_CONVERTER:
            return None
        return float(lease_time[:-1]) * LEASE_TIME_UNITS_CONVERTER[lease_time[-1]]

    def _set_timeout(self):
        if not self._lease_time_seconds:
            return
        self._timeout = datetime.now() + timedelta(seconds=self._lease_time_seconds)
        self._logger.info('Setting DHCP timeout at %s' % self._timeout)

    def _next_test(self):
        try:
            self._timeout = None
            name, func = self.tests.pop(0)
            self._logger.info('Running ' + name)
            func()
        except Exception as e:
            self._logger.error(str(e))
            self._finalize(exception=e)

    def _dhcp_port_toggle_test(self):
        self._set_timeout()
        if not self.host.connect_port(False):
            self._logger.error('disconnect port not enabled')
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
        self._logger.info('Testing dhcp range: ' + str(dhcp_range))
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
            self._logger.error('disconnect port not enabled')
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
        self._logger.info('Module finalizing')
        self._ip_callback = None
        self._file_handler.close()
        if not self._force_terminated:
            self.callback(return_code=return_code, exception=exception)

    def terminate(self):
        """Terminate this set of tests"""
        self._logger.info('Module terminating')
        self._force_terminated = True
        if self.docker_host.start_time:
            self.docker_host.terminate()
        self._finalize()

    def ip_listener(self, target_ip):
        """Respond to a ip notification event"""
        self._logger.info('ip notification %s' % target_ip)
        self.host.runner.ping_test(self.host.gateway.host, self.host.target_ip)
        if self._ip_callback:
            self._ip_callback()

    def heartbeat(self):
        if self._timeout and datetime.now() >= self._timeout:
            if self.docker_host.start_time:
                self.terminate()
                self.callback(exception=self._TIMEOUT_EXCEPTION)
            else:
                self._logger.error('DHCP times out after %ds lease time' % self._lease_time_seconds)
                self.tests = self.tests[-1:]
                self._next_test()
