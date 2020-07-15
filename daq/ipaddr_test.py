"""Test module encapsulating ip-address tests (including DHCP)"""

import time
import os
import logger

LOGGER = logger.get_logger('ipaddr')


class IpAddrTest:
    """Module for inline ipaddr tests"""

    DEFAULT_WAIT_SEC = 10

    # pylint: disable=too-many-arguments
    def __init__(self, host, target_port, tmpdir, test_name, module_config):
        self.host = host
        self.target_port = target_port
        self.tmpdir = tmpdir
        self.test_config = module_config.get('modules').get('ipaddr')
        self.test_name = test_name
        self.host_name = '%s%02d' % (test_name, self.target_port)
        self.log_path = os.path.join(self.tmpdir, 'nodes', self.host_name, 'activate.log')
        self.log_file = None
        self.callback = None
        self.tests = [
            self._dhcp_port_toggle_test,
            self._finalize
        ]

    def start(self, port, params, callback, finish_hook):
        """Start the ip-addr tests"""
        self.callback = callback
        LOGGER.debug('Target port %d starting ipaddr test %s', self.target_port, self.test_name)
        self.log_file = open(self.log_path, 'w')
        self._next_test()

    def _next_test(self):
        try:
            self.tests.pop(0)()
        except Exception as e:
            self._finalize(exception=e)

    def activate_log(self, message):
        """Log an activation message"""
        self.log_file.write(message + '\n')

    def _dhcp_port_toggle_test(self):
        self.activate_log('dhcp_port_toggle_test')
        self.host.connect_port(False)
        time.sleep(self.host.config.get("port_debounce_sec", 0) + 1)
        self.host.connect_port(True)

    def _finalize(self, exception=None):
        self.terminate()
        self.callback(exception=exception)

    def terminate(self):
        """Terminate this set of tests"""
        self.log_file.close()
        self.log_file = None

    def ip_listener(self, target_ip):
        """Respond to a ip notification event"""
        self.activate_log('ip notification %s' % target_ip)
        LOGGER.info("%s received ip %s" % (self.test_name, target_ip))
        self._next_test()
