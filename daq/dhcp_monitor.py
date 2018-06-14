"""Encapsulate DHCP monitor/startup"""

import logging
import re
import time

from clib import tcpdump_helper

LOGGER = logging.getLogger('dhcp')

class DhcpMonitor(object):
    """Class to handle DHCP monitoring"""

    DHCP_MAC_PATTERN = '> ([0-9a-f:]+), ethertype IPv4'
    DHCP_IP_PATTERN = 'Your-IP ([0-9.]+)'
    DHCP_PATTERN = '(%s)|(%s)' % (DHCP_MAC_PATTERN, DHCP_IP_PATTERN)
    DHCP_TIMEOUT_SEC = 240
    DHCP_THRESHHOLD_SEC = 20

    def __init__(self, runner, port_set, container, callback):
        self.runner = runner
        self.port_set = port_set
        self.callback = callback
        self.networking = container
        self.target_ip = None
        self.target_mac = None
        self.dhcp_traffic = None
        self.runner = None
        self.port_set = None
        self.intf_name = None
        self.callback = None
        self.test_start = None

    def start(self):
        """Start monitoring DHCP"""
        LOGGER.info('Set %d waiting for dhcp reply from %s...', self.port_set, self.networking.name)
        self.test_start = int(time.time())
        tcp_filter = "src port 67"
        helper = tcpdump_helper.TcpdumpHelper(self.networking, tcp_filter, packets=None,
                                              timeout=self.DHCP_TIMEOUT_SEC, blocking=False)
        self.dhcp_traffic = helper
        self.runner.monitor_stream(self.networking.name, self.dhcp_traffic.stream(),
                                   self._dhcp_line, hangup=self._dhcp_hangup,
                                   error=self._dhcp_error)

    def _dhcp_line(self):
        dhcp_line = self.dhcp_traffic.next_line()
        if not dhcp_line:
            return
        match = re.search(self.DHCP_PATTERN, dhcp_line)
        if match:
            self.target_ip = match.group(4)
            if self.target_ip:
                message = 'dhcp IP %s found, but no MAC address: %s' % (self.target_ip, dhcp_line)
                assert self.target_mac, message
                self._dhcp_success()
            else:
                self.target_mac = match.group(2)

    def cleanup(self, forget=True):
        """Cleanup any ongoing dhcp activity"""
        if self.dhcp_traffic:
            if forget:
                self.runner.monitor_forget(self.dhcp_traffic.stream())
            self.dhcp_traffic.terminate()
            self.dhcp_traffic = None

    def _dhcp_success(self):
        self.cleanup()
        delta = int(time.time()) - self.test_start
        LOGGER.info('Set %d received dhcp reply after %ds: %s is at %s',
                    self.port_set, delta, self.target_mac, self.target_ip)
        weak_result = delta > self.DHCP_THRESHHOLD_SEC
        state = 'weak' if weak_result else None
        self.callback(state, target_mac=self.target_mac, target_ip=self.target_ip)

    def _dhcp_hangup(self):
        self._dhcp_error(Exception('dhcp hangup'))

    def _dhcp_error(self, e):
        LOGGER.error('Set %d dhcp error: %s', self.port_set, e)
        self.cleanup(forget=False)
        self.callback('error', exception=e)
