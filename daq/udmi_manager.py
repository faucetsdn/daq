"""Module for managing a UDMI/MQTT connection to GCP IoT Core"""

from udmi.schema.event_discovery import Discovery

class UdmiManager:
    """Manager class for managing UDMI connection"""

    def __init__(self, config):
        self._config = config

    def discovery(self, device):
        LOGGER.info('Sending udmi discovery message for device %s', device.mac)
        message = Discovery()
