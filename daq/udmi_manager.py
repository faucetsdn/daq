"""Module for managing a UDMI/MQTT connection to GCP IoT Core"""

import logger
import utils

from proto import system_config_pb2 as sys_config

from udmi.agent.mqtt_manager import MqttManager
from udmi.schema.event_discovery import Discovery
from udmi.schema.event_audit import Audit

LOGGER = logger.get_logger('udmi')

class UdmiManager:
    """Manager class for managing UDMI connection"""

    def __init__(self, config):
        self._config = config.get('cloud_config', {})
        cloud_config = utils.dict_proto(self._config, sys_config.CloudConfig)
        if cloud_config.project_id:
            LOGGER.info('Creating mqtt connection to %s/%s/%s',
                        cloud_config.project_id, cloud_config.registry_id,
                        cloud_config.device_id)
            self._mqtt = MqttManager(cloud_config, self._on_message)
            self._mqtt.loop_start()
        else:
            LOGGER.info('No project_id defined, skipping mqtt client creation')
            self._mqtt = None

    def _send(self, message_type, message):
        LOGGER.debug('Sending udmi %s message', message_type)

    def _on_message(self, topic, message):
        LOGGER.info('Received udmi message on %s', topic)

    def discovery(self, device):
        """Handle a device discovery update"""
        LOGGER.info('Sending udmi discovery message for device')
        discovery = Discovery()
        self._send('discovery', discovery)

    def report(self, report):
        """Handle a device result report"""
        LOGGER.info('Sending udmi report message for device')
        audit = Audit()
        self._send('audit', audit)
