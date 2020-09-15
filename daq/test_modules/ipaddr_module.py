"""Test module encapsulating ip-address tests (including DHCP)"""

from __future__ import absolute_import
import logging

import time
import os
import copy
import logger
import docker_test

from .base_module import HostModule

_LOG_FORMAT = "%(asctime)s %(levelname)-7s %(message)s"

class IpAddrModule(HostModule):
    """Module for inline ipaddr tests"""

    def __init__(self, host, tmpdir, test_name, module_config):
        super().__init__(host, tmpdir, test_name, module_config)
        self.docker_host = docker_test.DockerTest(host, tmpdir, test_name, module_config)
        self.test_dhcp_ranges = copy.copy(self.test_config.get('dhcp_ranges', []))
        self._ip_callback = None
        self.tests = [
            ('dhcp port_toggle test', self._dhcp_port_toggle_test),
            ('dhcp multi subnet test', self._multi_subnet_test),
            ('ip change test', self._ip_change_test),
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

    def start(self, port, params, callback, finish_hook):
        """Start the ip-addr tests"""
        super().start(port, params, callback, finish_hook)
        self._logger.debug('Target device %s starting ipaddr test %s', self.device, self.test_name)
        self._next_test()

    def _next_test(self):
        try:
            name, func = self.tests.pop(0)
            self._logger.info('Running ' + name)
            func()
        except Exception as e:
            self._logger.error(str(e))
            self._finalize(exception=e)

    def _dhcp_port_toggle_test(self):
        if not self.host.connect_port(False):
            self.log('disconnect port not enabled')
            return
        time.sleep(self.host.config.get("port_debounce_sec", 0) + 1)
        self.host.connect_port(True)
        self._ip_callback = self._next_test

    def _multi_subnet_test(self):
        if not self.test_dhcp_ranges:
            self._next_test()
            return
        dhcp_range = self.test_dhcp_ranges.pop(0)
        self._logger.info('Testing dhcp range: ' + str(dhcp_range))
        args = (dhcp_range["start"], dhcp_range["end"], dhcp_range["prefix_length"])
        self.host.gateway.change_dhcp_range(*args)
        self._ip_callback = self._multi_subnet_test if self.test_dhcp_ranges else self._next_test

    def _ip_change_test(self):
        self.host.gateway.request_new_ip(self.host.target_mac)
        self._ip_callback = self._next_test

    def _analyze(self):
        self._ip_callback = None
        self.docker_host.start(self.port, self.params,
                               self._finalize, self._finish_hook)

    def _finalize(self, return_code=None, exception=None):
        self._logger.info('Module finalizing')
        self._ip_callback = None
        self._file_handler.close()
        if not self._force_terminated:
            self.callback(return_code=None, exception=exception)

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
        if self._ip_callback:
            self._ip_callback()
