"""Module to discover devices learnt on the bridge"""

from __future__ import absolute_import

from daq.proto.device_coupler_pb2 import DeviceDiscoveryEvent, DiscoveryEventType
from device_coupler.heartbeat_scheduler import HeartbeatScheduler
from device_coupler.ovs_helper import OvsHelper
from device_coupler.utils import get_logger


class DeviceDiscovery():
    """Device discovery helper for device coupler"""

    _POLLING_INTERVAL = 3

    def __init__(self, bridge, test_vlans, trunk_iface):
        self._ovs_helper = OvsHelper()
        self._logger = get_logger('device_discovery')
        self._bridge = bridge
        self._test_vlans = test_vlans
        self._polling_timer = None
        self._fdb_snapshot = None
        self._trunk_iface = trunk_iface
        self._trunk_ofport = None

    def setup(self):
        """Setup device discovery"""
        self._trunk_ofport = self._ovs_helper.get_interface_ofport(self._trunk_iface)
        self._fdb_snapshot = set()
        self._polling_timer = HeartbeatScheduler(self._POLLING_INTERVAL)
        self._polling_timer.add_callback(self.poll_forwarding_table)
        self._polling_timer.start()

    def cleanup(self):
        """Clean up device discovery"""
        if self._polling_timer:
            self._polling_timer.stop()

    def _process_entry(self, event):
        # Only process events for test vlans in config and on trunk port
        if event.port == self._trunk_ofport and event.vlan in self._test_vlans:
            print(event)

    def poll_forwarding_table(self):
        """Poll forwarding table and determine devices learnt/expired"""
        fdb_table = set(self._ovs_helper.get_forwarding_table(self._bridge))
        expired = self._fdb_snapshot - fdb_table
        discovered =  fdb_table - self._fdb_snapshot
        for entry in expired:
            event = self._build_device_discovery_event(entry, expire=True)
            self._process_entry(event)
        for entry in discovered:
            event = self._build_device_discovery_event(entry)
            self._process_entry(event)
        self._fdb_snapshot = fdb_table

    def _build_device_discovery_event(self, entry, expire=False):
        port, vlan, mac = entry
        event = DeviceDiscoveryEvent()
        event.port = int(port)
        event.vlan = int(vlan)
        event.mac = mac
        event.event_type = DiscoveryEventType.EXPIRY if expire else DiscoveryEventType.DISCOVERY
        return event



def main():
    pass


if __name__ == "__main__":
    main()
