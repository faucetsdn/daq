"""Module to run device coupler"""

from __future__ import absolute_import

from proto import system_config_pb2 as sys_config
from daq.proto.device_coupler_pb2 import DeviceDiscoveryEvent, DiscoveryEventType

from device_coupler.utils import get_logger, yaml_proto, write_yaml_file
from device_coupler.network_helper import NetworkHelper
from device_coupler.device_discovery import DeviceDiscovery

import time


class DeviceCoupler():
    """Main for device coupler"""

    def __init__(self, config):
        self._logger = get_logger('device_coupler')
        self._config = config
        self._test_vlans = list(config.test_vlans)
        self._network_helper = None
        self._device_discovery = None


    def setup(self):
        """Setup n/w"""
        self._network_helper = NetworkHelper(
            self._config.trunk_iface, self._config.bridge, self._test_vlans)
        self._network_helper.setup()
        self._device_discovery = DeviceDiscovery(
                self._config.bridge, self._test_vlans, self._config.trunk_iface)
        self._device_discovery.setup()


    def cleanup(self):
        """Clean up n/w"""
        self._network_helper.cleanup()
        self._device_discovery.cleeanup()


def main():
    config = yaml_proto("device_coupler/config/device_coupler_config.yaml", sys_config.DeviceCouplerConfig)
    device_coupler = DeviceCoupler(config)
    device_coupler.setup()
    while True:
        time.sleep(15)


if __name__ == "__main__":
    main()
