"""Module for managing a UDMI/MQTT connection to GCP IoT Core"""

import logger
import utils

from proto import system_config_pb2 as sys_config

from udmi.agent.mqtt_manager import MqttManager
from udmi.schema import Discovery, FamilyDiscoveryEvent, Audit

LOGGER = logger.get_logger('udmi')

class UdmiManager:
    """Manager class for managing UDMI connection"""

    def __init__(self, config):
        self._config = config.get('cloud_config', {})
        cloud_config = utils.dict_proto(self._config, sys_config.CloudConfig)
        if not cloud_config.project_id:
            LOGGER.info('No project_id defined, skipping mqtt client creation')
            self._mqtt = None
            return

        LOGGER.info('Creating mqtt connection to %s/%s/%s',
                    cloud_config.project_id, cloud_config.registry_id,
                    cloud_config.device_id)
        self._mqtt = MqttManager(cloud_config, on_message=self._on_message)
        self._mqtt.loop_start()

    def _send(self, message_type, message):
        LOGGER.debug('Sending udmi %s message', message_type)

    def _on_message(self, topic, message):
        LOGGER.info('Received udmi message on %s', topic)

    def discovery(self, device):
        """Handle a device discovery update"""
        discovery = Discovery()
        discovery.families = {}
        if device.mac:
            hwaddr = discovery.families.setdefault('hwaddr', FamilyDiscoveryEvent())
            hwaddr.id = device.mac
            hwaddr.group = device.assigned
            hwaddr.active = device.assigned == device.vlan
        if device.ip_info.ip_addr:
            inet = discovery.families.setdefault('inet', FamilyDiscoveryEvent())
            inet.id = device.ip_info.ip_addr
        if discovery.families:
            LOGGER.debug('Sending udmi discovery message for device %s', device.mac)
            self._send('discovery', discovery)

    def report(self, report):
        """Handle a device result report"""
        LOGGER.info('Sending udmi report message for device')
        audit = Audit()
        self._send('audit', audit)
