"""Collect Varz states"""

from __future__ import absolute_import

import argparse
import json
import prometheus_client.parser
import requests
import sys
import time

import logger

LOGGER = logger.get_logger('varzstate')
DEFAULT_VARZ_ADDRESS = 'localhost'
DEFAULT_FAUCET_VARZ_PORT = 9302
DEFAULT_GAUGE_VARZ_PORT = 9303


class VarzStateCollector:
    """Collecting varz states"""

    METRIC_RETRY_INTERVAL_SEC = 3

    def __init__(self, varz_address, faucet_varz_port, gauge_varz_port):
        endpoint_address = varz_address or DEFAULT_VARZ_ADDRESS
        self._faucet_varz_endpoint = (
            f'http://{endpoint_address}:{faucet_varz_port or DEFAULT_FAUCET_VARZ_PORT}')
        self._gauge_varz_endpoint = (
            f'http://{endpoint_address}:{gauge_varz_port or DEFAULT_GAUGE_VARZ_PORT}')

    def retry_get_faucet_metrics(self, target_metrics, retries=3):
        return self._retry_get_metrics(self._faucet_varz_endpoint, target_metrics, retries)

    def retry_get_gauge_metrics(self, target_metrics, retries=3):
        return self._retry_get_metrics(self._gauge_varz_endpoint, target_metrics, retries)

    def _retry_get_metrics(self, endpoint, target_metrics, retries):
        """Get a list of target metrics with configured number of retries"""
        for retry in range(retries):
            try:
                return self._get_metrics(endpoint, target_metrics)
            except Exception as e:
                LOGGER.error(
                    'Could not retrieve metrics after %d retries: %s', retry, e)
                time.sleep(self.METRIC_RETRY_INTERVAL_SEC)
        raise Exception(f'Could not retrieve metrics {target_metrics} after {retries} retries')

    def _get_metrics(self, endpoint, target_metrics):
        """Get a list of target metrics"""
        metric_map = {}

        response = requests.get(endpoint)
        if response.status_code != requests.status_codes.codes.ok:  # pylint: disable=no-member
            raise Exception(f'Error response code: {response.status_code}')

        content = response.content.decode('utf-8', 'strict')
        metrics = prometheus_client.parser.text_string_to_metric_families(content)
        for metric in [m for m in metrics if m.name in target_metrics]:
            metric_map[metric.name] = metric

        return metric_map


def parse_args(raw_args):
    """Parse sys args"""
    parser = argparse.ArgumentParser(description='Varz collector')
    parser.add_argument('-a', '--address', type=str, default=DEFAULT_VARZ_ADDRESS,
                        help='Varz endpoint address')
    parser.add_argument('-f', '--faucet-varz-port', type=str, default=DEFAULT_FAUCET_VARZ_PORT,
                        help='Faucet varz port')
    parser.add_argument('-g', '--gauge-varz-port', type=str, default=DEFAULT_GAUGE_VARZ_PORT,
                        help='Gauge varz port')
    parser.add_argument('-l', '--label-matches', type=str,
                        help='Only output samples whose labels match specified key value pairs')
    parser.add_argument('-x', '--faucet-target-metrics', type=str,
                        help='Faucet target metrics separated by comma')
    parser.add_argument('-y', '--gauge-target-metrics', type=str,
                        help='Gauge target metrics separated by comma')
    parser.add_argument('-o', '--output-file', type=str,
                        help='Output file')
    return parser.parse_args(raw_args)


def report_metrics(metrics, label_matches):
    metrics_map = {}

    for metric in metrics.values():
        samples = []
        for sample in metric.samples:
            if label_matches.items() <= sample.labels.items():
                sample_map = {'labels': sample.labels, 'value': sample.value}
                samples.append(sample_map)
        samples.sort(key=lambda map: str(map['labels']))
        metrics_map[metric.name] = {'samples': samples}

    return metrics_map

def main():
    args = parse_args(sys.argv[1:])
    varz_collector = VarzStateCollector(
        args.address, args.faucet_varz_port, args.gauge_varz_port)
    varz_metrics_map = {}

    if args.faucet_target_metrics:
        faucet_target_metrics = args.faucet_target_metrics.split(',')
        faucet_varz_metrics = varz_collector.retry_get_faucet_metrics(faucet_target_metrics)
        varz_metrics_map['faucet_metrics'] = report_metrics(faucet_varz_metrics)

    if args.gauge_target_metrics:
        gauge_target_metrics = args.gauge_target_metrics.split(',')
        gauge_varz_metrics = varz_collector.retry_get_gauge_metrics(gauge_target_metrics)
        varz_metrics_map['gauge_metrics'] = report_metrics(gauge_varz_metrics)

    if args.output_file:
        with open(args.output_file, 'w') as file:
            json.dump(varz_metrics_map, file)
    else:
        print(json.dumps(varz_metrics_map))

if __name__ == '__main__':
    main()
