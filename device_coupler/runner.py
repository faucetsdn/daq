"""Module to run device coupler"""

from __future__ import absolute_import

from proto import system_config_pb2 as sys_config
from daq.proto.device_coupler_pb2 import DiscoveryEventType

from device_coupler.utils import get_logger, yaml_proto
from device_coupler.network_helper import NetworkHelper
from device_coupler.device_discovery import DeviceDiscovery
from device_coupler.daq_client import DAQClient
from device_coupler.ovs_helper import OvsHelper

from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

import argparse
import time


class DeviceCoupler():
    """Main for device coupler"""

    _WORKER_TIMEOUT = 10
    _WORKER_COUNT = 3
    _OVS_BRIDGE = "dev_br0"

    def __init__(self, config):
        self._logger = get_logger('device_coupler')
        self._test_vlans = (config.run_trigger.vlan_start, config.run_trigger.vlan_end)
        self._trunk_iface = config.switch_setup.data_intf
        self._daq_grpc_ip = config.run_trigger.runner_service_ip
        self._daq_grpc_port = config.device_reporting.server_port
        self._network_helper = None
        self._device_discovery = None
        self._daq_client = None
        self._event_queue = None
        self._workers_executor = None
        self._source_ip = None
        self._running = None

    def setup(self):
        """Setup device coupler"""
        self._ovs_helper = OvsHelper()

        self._network_helper = NetworkHelper(
            self._trunk_iface, self._OVS_BRIDGE, self._test_vlans)
        self._network_helper.setup()

        self._event_queue = Queue()
        self._workers_executor = ThreadPoolExecutor(max_workers=self._WORKER_COUNT)
        self._device_discovery = DeviceDiscovery(
            self._OVS_BRIDGE, self._test_vlans,
            self._trunk_iface, self.add_event_to_queue)

        self._source_ip = self._ovs_helper.get_interface_ip()
        target_str = '%s:%s' % (self._daq_grpc_ip, self._daq_grpc_port)
        self._daq_client = DAQClient(target_str, self._source_ip, self._OVS_BRIDGE)

    def start(self):
        """Start device coupler"""
        self._running = True
        self._device_discovery.start()
        self._daq_client.start()
        self._logger.info('Starting %s workers', self._WORKER_COUNT)
        for index in range(self._WORKER_COUNT):
            self._workers_executor.submit(self._process_event_queue)

    def cleanup(self):
        """Clean up device coupler"""
        self._running = False
        self._workers_executor.shutdown()
        self._daq_client.stop()
        self._device_discovery.cleanup()
        self._network_helper.cleanup()
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
                    port = self._get_device_port(event.vlan)
                    self._daq_client.process_device_discovery(event.mac, event.vlan, port)
                else:
                    self._daq_client.process_device_expiry(event.mac)
            except Empty:
                # Worker timeout. Do nothing
                pass

    def _get_device_port(self, vlan):
        """Mapping for VLAN to ports uses first VLAN of accepted test VLAN range."""
        # TODO: Change once device_coupler can reliably access switch port number
        return vlan - self._test_vlans[0] + 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help="DAQ config file", type=str)

    args = parser.parse_args()

    config = yaml_proto(
        args.config, sys_config.DaqConfig)
    device_coupler = DeviceCoupler(config)
    device_coupler.setup()
    device_coupler.start()
    # Block for eternity
    while True:
        time.sleep(2400)


if __name__ == "__main__":
    main()
