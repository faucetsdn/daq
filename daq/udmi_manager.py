"""Module for managing a UDMI/MQTT connection to GCP IoT Core"""

class UdmiManager:
    """Manager class for managing UDMI connection"""

    def __init__(self, config):
        self._config = config
