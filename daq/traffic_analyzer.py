"""Traffic analysis module"""

from __future__ import absolute_import

import argparse
import json
import logging
import sys
import threading
import time

from acl_state_collector import AclStateCollector
import logger
from utils import dict_proto, proto_dict
from varz_state_collector import VarzStateCollector

from proto.acl_counting_pb2 import DeviceRuleCounts

from faucet import config_parser
from forch.proto.devices_state_pb2 import DevicePlacement

LOGGER = logger.get_logger('ta')


class TrafficAnalyzer:
    """Analyzing traffic statistics"""

    _RULE_COUNT_METRIC = 'flow_packet_count_port_acl'
    _DEVICE_LEARNING_METRIC = 'learned_l2_port'
    _SEC_SWITCH = 'sec'
    _PERIODIC_TASKS_INTERVAL_SEC = 30

    def __init__(self, device_specs_file, faucet_config_file):
        self._device_specs_file = device_specs_file
        self._faucet_config_file = faucet_config_file
        self._acl_state_collector = AclStateCollector()
        self._varz_state_collector = VarzStateCollector()
        self._duts = set()
        self._device_placements = {}
        self._lock = threading.Lock()
        self._initialized = False
        self._run = True

    def initialize(self):
        self._reload_device_specs()
        self._initialized = True

    def start(self):
        """Start periodic tasks"""
        assert self._initialized
        self._run = True
        threading.Thread(target=self._periodic_tasks, daemon=True).start()

    def stop(self):
        self._run = False

    def get_device_rule_counts(self):
        """Return the rule counts for all the learned devices"""
        with self._lock:
            return dict_proto(self._get_device_rule_counts(), DeviceRuleCounts)

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

    def _get_rule_count_metric(self):
        try:
            metrics = self._varz_state_collector.retry_get_gauge_metrics([self._RULE_COUNT_METRIC])
        except Exception as e:
            return None, str(e)

        rule_count_metric = metrics.get(self._RULE_COUNT_METRIC)

        if not rule_count_metric:
            error = 'No flow_packet_count_port_acl metric available'
            return None, error

        return rule_count_metric, None

    def _reload_faucet_config(self):
        _, _, dps_config, _ = config_parser.dp_parser(self._faucet_config_file, 'fconfig')
        switches_config = {str(dp): dp for dp in dps_config}
        self._acl_state_collector.update_switch_configs(switches_config)

    def _reload_device_specs(self):
        with open(self._device_specs_file) as file:
            device_specs = json.load(file)
            self._duts = set(device_specs.get('macAddrs', {}).keys())
            LOGGER.info('Loaded %s devices', len(self._duts))

    def _update_device_placements(self):
        try:
            metrics = self._varz_state_collector.retry_get_faucet_metrics(
                [self._DEVICE_LEARNING_METRIC])
        except Exception as e:
            LOGGER.error('Could not get %s metric: %s', self._DEVICE_LEARNING_METRIC, e)
            
        device_learning_metric = metrics.get(self._DEVICE_LEARNING_METRIC)
        if not device_learning_metric:
            LOGGER.info('No devices are learned')

        device_placements = {}
        for sample in device_learning_metric.samples:
            if sample.labels.get('dp_name' != self._SEC_SWITCH):
                continue

            mac = sample.labels.get('eth_src')
            if mac not in self._duts:
                continue

            port = int(sample.value)
            device_placements[mac] = DevicePlacement(switch=self._SEC_SWITCH, port=port)

    def _periodic_tasks(self):
        if not self._run:
            return

        with self._lock:
            self._reload_faucet_config()
            self._update_device_placements()
        threading.Timer(self._PERIODIC_TASKS_INTERVAL_SEC, self._periodic_tasks).start()


def parse_args(raw_args):
    """Parse sys args"""
    parser = argparse.ArgumentParser(description='Varz collector')
    parser.add_argument('-f', '--faucet-config', type=str, default='inst/faucet.yaml',
                        help='Faucet config file')
    parser.add_argument('device_specs', type=str, help='Device specs file')
    parser.add_argument('output_file', type=str, help='Output file for device rule counts')
    return parser.parse_args(raw_args)

def main():
    args = parse_args(sys.argv[1:])
    logging.basicConfig(level='INFO')

    logging.info(
        'Initializing traffic analyzer with: %s, %s', args.device_specs, args.faucet_config)
    traffic_analyzer = TrafficAnalyzer(args.device_specs, args.faucet_config)
    traffic_analyzer.initialize()
    traffic_analyzer.start()

    try:
        time.sleep(10)
        logging.info(
            'Traffic analyzer started. Periodically saving device rule counts to file %s.',
            args.output_file)
        while True:
            device_rule_counts = proto_dict(traffic_analyzer.get_device_rule_counts())
            with open(args.output_file, 'w') as file:
                json.dump(device_rule_counts, file)
            time.sleep(30)
    except KeyboardInterrupt:
        logging.info('Keyboard interrupt. Exiting.')

    traffic_analyzer.stop()


if __name__ == '__main__':
    main()
