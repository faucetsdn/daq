"""Test module encapsulating ip-address tests (including DHCP)"""

from __future__ import absolute_import
import time
import os
import copy
import logger

LOGGER = logger.get_logger('ipaddr')


class IpAddrTest:
    """Module for inline ipaddr tests"""

    # pylint: disable=too-many-arguments
    def __init__(self, host, target_port, tmpdir, test_name, module_config):
        self.host = host
        self.target_port = target_port
        self.tmpdir = tmpdir
        self.test_config = module_config.get('modules').get('ipaddr')
        self.test_dhcp_ranges = copy.copy(self.test_config.get('dhcp_ranges', []))
        self.test_name = test_name
        self.host_name = '%s%02d' % (test_name, self.target_port)
        self.log_path = os.path.join(self.tmpdir, 'nodes', self.host_name, 'activate.log')
        self.log_file = None
        self.callback = None
        self._ip_callback = None
        self.tests = [
            ('dhcp port_toggle test', self._dhcp_port_toggle_test),
            ('dhcp multi subnet test', self._multi_subnet_test),
            ('ip change test', self._ip_change_test),
            ('finalize', self._finalize)
        ]

    def start(self, port, params, callback, finish_hook):
        """Start the ip-addr tests"""
        self.callback = callback
        LOGGER.debug('Target port %d starting ipaddr test %s', self.target_port, self.test_name)
        self.log_file = open(self.log_path, 'w')
        self._next_test()

    def _next_test(self):
        try:
            name, func = self.tests.pop(0)
            self.log('Running ' + name)
            func()
        except Exception as e:
            self.log(str(e))
            self._finalize(exception=e)

    def log(self, message):
        """Log an activation message"""
        LOGGER.info(message)
        self.log_file.write(message + '\n')

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
        self.log('Testing dhcp range: ' + str(dhcp_range))
        args = (dhcp_range["start"], dhcp_range["end"], dhcp_range["prefix_length"])
        self.host.gateway.change_dhcp_range(*args)
        self._ip_callback = self._multi_subnet_test if self.test_dhcp_ranges else self._next_test

    def _ip_change_test(self):
        self.host.gateway.request_new_ip(self.host.target_mac)
        self._ip_callback = self._next_test

    def _finalize(self, exception=None):
        self.terminate()
        self.callback(exception=exception)

    def terminate(self):
        """Terminate this set of tests"""
        self.log('Module terminating')
        self.log_file.close()
        self.log_file = None

    def ip_listener(self, target_ip):
        """Respond to a ip notification event"""
        self.log('ip notification %s' % target_ip)
        if self._ip_callback:
            self._ip_callback()
