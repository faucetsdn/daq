"""Gateway module for device testing"""
from __future__ import absolute_import

import os

from mininet.node import Host

import dhcp_monitor
import logger
from base_gateway import BaseGateway

LOGGER = logger.get_logger('gateway')


class ExternalGatewayHost(Host):
    """External Gateway Host class"""
    def activate(self):
        """To match other Host classes"""


class ExternalGateway(BaseGateway):
    """Gateway collection class for managing testing services"""

    def __init__(self, *args):
        super().__init__(*args)
        self._scan_monitor = None
        self.dhcp_monitor = None

    def _initialize(self):
        super()._initialize()
        log_file = os.path.join(self.tmpdir, 'dhcp_monitor.txt')
        self.dhcp_monitor = dhcp_monitor.DhcpMonitor(self.runner, self.runner.network.pri,
                                                     self._dhcp_callback, log_file=log_file,
                                                     intf_name=self.runner.network.ext_intf)
        self.dhcp_monitor.start()

    def _get_host_class(self):
        return ExternalGatewayHost
