"""Traffic analysis module"""

from __future__ import absolute_import

import json
import threading

from acl_state_collector import AclStateCollector
import logger
from utils import dict_proto
from varz_state_collector import VarzStateCollector

from proto.acl_counts_pb2 import DeviceRuleCounts

from faucet import config_parser

LOGGER = logger.get_logger('ta')


class TrafficAnalyzer:
    """Analyzing traffic statistics"""

    RULE_COUNT_METRIC = 'flow_packet_count_port_acl'

    def __init__(self, faucet_config_file, device_specs_file):
        self._faucet_config_file = faucet_config_file
        self._device_specs_file = device_specs_file
        self._acl_state_collector = AclStateCollector()
        self._varz_state_collector = VarzStateCollector()
        self._duts = []
        self._device_placements = {}

    def get_acl_counts(self):
        """Return the rule counts for all the learned devices"""
        return dict_proto(self._get_acl_counts(), DeviceRuleCounts)

    def _get_device_rule_counts(self):
        port_acl_metrics, error = self._get_rule_count_metric()

        if error:
            LOGGER.error(error)
            return {'error': error}

        device_rule_counts = {}

        for mac, device_placement in self._device_placements.items():
            rule_counts_map = device_rule_counts.setdefault('device_mac_rules', {})
            rule_counts_map[mac] = self._acl_state_collector.get_port_acl_count(
                device_placement.switch, device_placement.port, port_acl_metrics.samples)

        return device_rule_counts

    def _reload_faucet_config(self):
        _, _, dps_config, _ = config_parser.dp_parser(self._faucet_config_file, 'fconfig')
        switches_config = {str(dp): dp for dp in dps_config}
        self._acl_state_collector.update_switch_configs(switches_config)

    def _reload_device_specs(self):



    def _get_rule_count_metric(self):
        try:
            metrics = self._varz_state_collector.retry_get_gauge_metrics([RULE_COUNT_METRIC])
        except Exception as e:
            return None, str(e)

        rule_count_metric = metrics.get(RULE_COUNT_METRIC)

        if not rule_count_metric:
            error = 'No flow_packet_count_port_acl metric available'
            return None, error

        return rule_count_metric, None