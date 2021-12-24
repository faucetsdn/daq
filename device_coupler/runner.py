"""Module to run device coupler"""

from __future__ import absolute_import

from proto import system_config_pb2 as sys_config
from daq.proto.device_coupler_pb2 import DiscoveryEventType

from device_coupler.utils import get_logger, yaml_proto
from device_coupler.network_helper import NetworkHelper
from device_coupler.device_discovery import DeviceDiscovery
from device_coupler.daq_client import DAQClient
from device_coupler.ovs_helper import OvsHelper

from queue import Queue, Empty

import time
import threading


class DeviceCoupler():
    """Main for device coupler"""

    _WORKER_TIMEOUT = 10
    _WORKER_COUNT = 3

    def __init__(self, config):
        self._logger = get_logger('device_coupler')
        self._config = config
        self._test_vlans = list(config.test_vlans)
        self._network_helper = None
        self._device_discovery = None
        self._daq_client = None
        self._event_queue = None
        self._running = None
        self._workers = None
        self._source_ip = None

    def setup(self):
        """Setup device coupler"""
        self._running = True
        self._ovs_helper = OvsHelper()

        self._network_helper = NetworkHelper(
            self._config.trunk_iface, self._config.bridge, self._test_vlans)
        self._network_helper.setup()

        self._event_queue = Queue()
        self._build_worker_threads(self._process_event_queue, self._WORKER_COUNT)
        self._device_discovery = DeviceDiscovery(
            self._config.bridge, self._test_vlans,
            self._config.trunk_iface, self.add_event_to_queue)

        self._source_ip = self._ovs_helper.get_interface_ip()
        target_str = '%s:%s' % (self._config.target_ip, self._config.target_port)
        self._daq_client = DAQClient(target_str, self._source_ip, self._config.bridge)

    def start(self):
        """Start device coupler"""
        self._device_discovery.start()
        self._daq_client.start()
        self._logger.info('Starting %s workers', len(self._workers))
        for worker in self._workers:
            worker.start()

    def cleanup(self):
        """Clean up device coupler"""
        self._daq_client.stop()
        self._device_discovery.cleanup()
        self._network_helper.cleanup()
        self._running = False
        for worker in self._workers:
            worker.join()
        self._logger.info('Cleanup complete')

    def add_event_to_queue(self, event):
        """Add event to queue for processing"""
        self._event_queue.put(event)

    def _process_event_queue(self):
        while self._running:
            try:
                event = self._event_queue.get(timeout=self._WORKER_TIMEOUT)
                self._logger.info(event)
                if event.event_type == DiscoveryEventType.DISCOVERY:
                    self._daq_client.process_device_discovery(event.mac, event.vlan)
                else:
                    self._daq_client.process_device_expiry(event.mac)
            except Empty:
                # Worker thread timeout. Do nothing
                self._logger.info('Anurag worker timeout')
                pass

    def _build_worker_threads(self, method, count):
        self._workers = []
        for index in range(count):
            self._workers.append(threading.Thread(target=method))


def main():
    config = yaml_proto(
        "device_coupler/config/device_coupler_config.yaml", sys_config.DeviceCouplerConfig)
    device_coupler = DeviceCoupler(config)
    device_coupler.setup()
    device_coupler.start()
    time.sleep(400)
    device_coupler.cleanup()


if __name__ == "__main__":
    main()
