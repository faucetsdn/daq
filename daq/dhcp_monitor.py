"""Encapsulate DHCP monitor/startup"""

import re
import time

import logger
from clib import tcpdump_helper
from host import MODE

LOGGER = logger.get_logger('dhcp')


class DhcpMonitor:
    """Class to handle DHCP monitoring"""

    DHCP_START_PATTERN = 'BOOTP/DHCP'
    DHCP_IP_PATTERN = 'Your-IP ([0-9.]+)'
    DHCP_MAC_PATTERN = 'Client-Ethernet-Address ([a-z0-9:]+)'
    DHCP_TYPE_PATTERN = 'DHCP-Message Option 53, length 1: ([a-zA-Z]+)'
    DHCP_PATTERN = '(%s)|(%s)|(%s)|(%s)' % (DHCP_START_PATTERN,
                                            DHCP_IP_PATTERN,
                                            DHCP_MAC_PATTERN,
                                            DHCP_TYPE_PATTERN)
    DHCP_THRESHHOLD_SEC = 80

    # pylint: disable=too-many-arguments
    def __init__(self, runner, host, callback, log_file=None, intf_name=None):
        self.runner = runner
        self.callback = callback
        self.host = host
        self.intf_name = intf_name if intf_name else host.intf().name
        self.name = host.name
        self.log_file = log_file
        self.dhcp_traffic = None
        self.scan_start = None
        self.device_dhcps = {}
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
                                              timeout=None, blocking=False,
                                              intf_name=self.intf_name)
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
            LOGGER.debug('dhcp_line: %s', dhcp_line.strip())
            if match.group(1):
                self.target_mac = None
                self.target_ip = None
                LOGGER.debug('Reset dhcp')
            elif match.group(2):
                assert not self.target_ip
                self.target_ip = match.group(3)
                LOGGER.debug('Found ip %s', self.target_ip)
            elif match.group(4):
                assert not self.target_mac
                self.target_mac = match.group(5)
                LOGGER.debug('Found mac %s', self.target_mac)
            elif match.group(6):
                LOGGER.debug('Message type %s', match.group(7))
                self._dhcp_complete(match.group(7))
            else:
                LOGGER.info('Unknown dhcp match: %s', dhcp_line.strip())

    def cleanup(self):
        """Cleanup any ongoing dhcp activity"""
        if self.dhcp_log:
            self.dhcp_log.close()
            self.dhcp_log = None
        if self.dhcp_traffic:
            self.runner.monitor_forget(self.dhcp_traffic.stream())
            self.dhcp_traffic.terminate()
            self.dhcp_traffic = None

    def _dhcp_complete(self, dhcp_type):
        if dhcp_type not in ('ACK', 'Offer'):
            return
        assert self.target_ip, 'dhcp missing ip address'
        assert self.target_mac, 'dhcp missing mac address'
        delta = int(time.time()) - self.device_dhcps.get(self.target_mac, self.scan_start)
        LOGGER.info('DHCP monitor %s received %s reply after %ds: %s/%s',
                    self.name, dhcp_type, delta, self.target_ip, self.target_mac)
        mode = MODE.LONG if delta > self.DHCP_THRESHHOLD_SEC else MODE.DONE
        target = {
            'type': dhcp_type,
            'ip': self.target_ip,
            'mac': self.target_mac,
            'delta': delta
        }
        if dhcp_type == 'ACK':
            self.device_dhcps[self.target_mac] = int(time.time())
        self.callback(mode, target)

    def _dhcp_hangup(self):
        self.dhcp_traffic = None
        self._dhcp_error(Exception('dhcp hangup'))

    def _dhcp_error(self, e):
        LOGGER.error('DHCP monitor %s error: %s', self.name, e)
        if self.dhcp_log:
            self.dhcp_log.write('Monitor error %s\n' % e)
        self.cleanup()
        self.callback('error', None, exception=e)
