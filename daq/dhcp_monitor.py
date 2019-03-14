"""Encapsulate DHCP monitor/startup"""

import logging
import re
import time

from clib import tcpdump_helper

LOGGER = logging.getLogger('dhcp')

class DhcpMonitor():
    """Class to handle DHCP monitoring"""

    DHCP_IP_PATTERN = 'Your-IP ([0-9.]+)'
    DHCP_TYPE_PATTERN = 'DHCP-Message Option 53, length 1: ([a-zA-Z]+)'
    DHCP_MAC_PATTERN = 'Client-Ethernet-Address ([a-z0-9:]+)'
    DHCP_PATTERN = '(%s)|(%s)|(%s)' % (DHCP_IP_PATTERN, DHCP_TYPE_PATTERN, DHCP_MAC_PATTERN)
    DHCP_THRESHHOLD_SEC = 80

    def __init__(self, runner, host, callback, log_file=None):
        self.runner = runner
        self.callback = callback
        self.host = host
        self.name = host.name
        self.log_file = log_file
        self.dhcp_traffic = None
        self.intf_name = None
        self.scan_start = None
        self.target_ip = None
        self.target_mac = None
        self.dhcp_log = None

    def start(self):
        """Start monitoring DHCP"""
        LOGGER.info('DHCP monitor %s waiting for replies...', self.name,)
        if self.log_file:
            LOGGER.debug('Logging results to %s', self.log_file)
            self.dhcp_log = open(self.log_file, "w")
        self.scan_start = int(time.time())
        # Because there's buffering somewhere, can't reliably filter out DHCP with "src port 67"
        tcp_filter = ""
        helper = tcpdump_helper.TcpdumpHelper(self.host, tcp_filter, packets=None,
                                              timeout=None, blocking=False)
        self.dhcp_traffic = helper
        self.runner.monitor_stream(self.name, self.dhcp_traffic.stream(),
                                   self._dhcp_line, hangup=self._dhcp_hangup,
                                   error=self._dhcp_error)

    def _dhcp_line(self):
        dhcp_line = self.dhcp_traffic.next_line()
        if not dhcp_line:
            return
        if self.dhcp_log:
            self.dhcp_log.write(dhcp_line)
        match = re.search(self.DHCP_PATTERN, dhcp_line)
        if match:
            if match.group(2):
                self.target_ip = match.group(2)
            if match.group(4) == "ACK":
                self._dhcp_success()
            if match.group(6):
                self.target_mac = match.group(6)

    def cleanup(self, forget=True):
        """Cleanup any ongoing dhcp activity"""
        if self.dhcp_log:
            self.dhcp_log.close()
            self.dhcp_log = None
        if self.dhcp_traffic:
            if forget:
                self.runner.monitor_forget(self.dhcp_traffic.stream())
            self.dhcp_traffic.terminate()
            self.dhcp_traffic = None

    def _dhcp_success(self):
        assert self.target_ip, 'dhcp ACK missing ip address'
        assert self.target_mac, 'dhcp ACK missing mac address'
        delta = int(time.time()) - self.scan_start
        LOGGER.debug('DHCP monitor %s received reply after %ds: %s/%s',
                     self.name, delta, self.target_ip, self.target_mac)
        state = 'long' if delta > self.DHCP_THRESHHOLD_SEC else None
        target = {
            'ip': self.target_ip,
            'mac': self.target_mac,
            'delta': delta
        }
        self.callback(state, target)
        self.target_ip = None
        self.target_mac = None
        self.scan_start = int(time.time())

    def _dhcp_hangup(self):
        self._dhcp_error(Exception('dhcp hangup'))

    def _dhcp_error(self, e):
        LOGGER.error('DHCP monitor %s error: %s', self.name, e)
        if self.dhcp_log:
            self.dhcp_log.write('Monitor error %s\n' % e)
        self.cleanup(forget=False)
        self.callback('error', None, exception=e)
