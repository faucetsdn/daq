"""Module for managing a UDMI/MQTT connection to GCP IoT Core"""

import logger
from udmi.schema.event_discovery import Discovery
from udmi.schema.event_audit import Audit

LOGGER = logger.get_logger('udmi')

class UdmiManager:
    """Manager class for managing UDMI connection"""

    def __init__(self, config):
        self._config = config

    def _send(self, message_type, message):
        LOGGER.debug('Sending udmi %s message', message_type)

    def discovery(self, device):
        """Handle a device discovery update"""
        LOGGER.info('Sending udmi discovery message for device %s', device.mac)
        discovery = Discovery()
        self._send('discovery', discovery)

    def report(self, report):
        """Handle a device result report"""
        LOGGER.info('Sending udmi report message for device %s', report.mac)
        audit = Audit()
        self._send('audit', audit)
