"""Module for managing a UDMI/MQTT connection to GCP IoT Core"""

from __future__ import absolute_import

import json
import logger
import utils

from proto import system_config_pb2 as sys_config

try:
    from udmi.agent.mqtt_manager import MqttManager
    from udmi.schema import Discovery, FamilyDiscoveryEvent, Audit
except ImportError:
    MqttManager = None

LOGGER = logger.get_logger('udmi')


class UdmiManager:
    """Manager class for managing UDMI connection"""

    def __init__(self, config, mqtt_factory=MqttManager):
        self._config = config.get('cloud_config', {})
        cloud_config = utils.dict_proto(self._config, sys_config.CloudConfig)
        if not cloud_config.project_id:
            LOGGER.info('No project_id defined, skipping mqtt client creation')
            self._mqtt = None
            return

        assert mqtt_factory, 'missing mqtt_factory import/definition'

        LOGGER.info('Creating mqtt connection to %s/%s/%s',
                    cloud_config.project_id, cloud_config.registry_id,
                    cloud_config.device_id)
        self._mqtt = mqtt_factory(cloud_config, on_message=self._on_message)
        self._mqtt.loop_start()

    def _send(self, message_type, message):
        LOGGER.debug('Sending udmi %s message', message_type)
        self._mqtt.publish(message_type, json.dumps(message.to_dict()))

    def _on_message(self, topic, message):
        LOGGER.info('Received udmi message on %s', topic)

    def discovery(self, device):
        """Handle a device discovery update"""
        if not self._mqtt:
            return
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
            LOGGER.info('Sending udmi discovery message for device %s', device.mac)
            self._send('discovery', discovery)

    def report(self, report):
        """Handle a device result report"""
        if not self._mqtt:
            return
        audit = Audit()
        # TODO: Define Audit message and fill in with report results.
        self._send('audit', audit)
