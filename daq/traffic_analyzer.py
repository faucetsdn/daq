"""Traffic statistics analyzer"""

from acl_state_collector import AclStateCollector
import logger
from utils import dict_proto

from proto.acl_counts_pb2 import AclCounts

from faucet import config_parser

LOGGER = logger.get_logger('ta')


class TrafficAnalyzer:
    def __init__(self, faucet_config_file):
        self._faucet_config_file = faucet_config_file
        self._acl_state_collector = AclStateCollector()
        self._device_placements = {}

    def get_acl_counts(self):
        """Return the ACL counts for all the learned devices"""
        return dict_proto({'devices': self._get_acl_counts()}, AclCounts)

    def _get_acl_counts(self):
        acl_counts = {}

        port_acl_metrics = self._get_metrics().get('flow_packet_count_port_acl')
        if not port_acl_metrics:
            LOGGER.warning('No flow_packet_count_port_acl metric available')
            return acl_counts

        for mac, device_placement in self._device_placements.items():
            acl_counts[mac] = AclStateCollector.get_port_acl_count(
                device_placement.switch, device_placement.port, port_acl_metrics.samples)

        return acl_counts

    def reload_faucet_config(self):
        """Reload Faucet DPs config"""
        _, _, dps_config, _ = config_parser.parse_dps(self._faucet_config_file)
        switches_config = {str(dp): dp for dp in dps_config}
        self._acl_state_collector.update_switch_configs(switches_config)
