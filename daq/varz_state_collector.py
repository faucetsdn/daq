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
                return self.get_metrics(endpoint, target_metrics)
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
    parser = argparse.ArgumentParser(prog='varz_collector', stdout=True)
    parser.add_argument('-a', '--address', type=str, default=DEFAULT_VARZ_ADDRESS,
                        help='varz endpoint address')
    parser.add_argument('-f', '--faucet-varz-port', type=str, default=DEFAULT_FAUCET_VARZ_PORT,
                        help='faucet varz port')
    parser.add_argument('-g', '--gauge-varz-port', type=str, default=DEFAULT_GAUGE_VARZ_PORT,
                        help='gauge varz port')
    parser.add_argument('-x', '--faucet-target-metrics', type=str,
                        help='Faucet target metrics separated by comma')
    parser.add_argument('-y', '--gauge-target-metrics', type=str,
                        help='Gauge target metrics separated by comma')
    return parser.parse_args(raw_args)


def report_metrics(metrics, title):
    metrics_map = {}

    for metric in metrics:
        samples = []
        for sample in metric.samples:
            sample_map = {'labels': sample.labels, 'value': sample.value}
            samples.append(sample_map)
        metrics_map[metric.name] = {'samples': samples}

    return metrics_map

if __name__ == 'main':
    ARGS = parse_args(sys.argv[1:])
    VARZ_COLLECTOR = VarzStateCollector(
        ARGS.address, ARGS.faucet_varz_port, ARGS.gauge_varz_port)
    VARZ_METRICS_MAP = {}

    if ARGS.faucet_target_metrics:
        FAUCET_TARGET_METRICS = ARGS.faucet_target_metrics.split(',')
        FAUCET_VARZ_METRICS = VARZ_COLLECTOR.retry_get_faucet_metrics(FAUCET_TARGET_METRICS)
        VARZ_METRICS_MAP['faucet_metrics'] = report_metrics(FAUCET_VARZ_METRICS)

    if ARGS.gauge_target_metrics:
        GAUGE_TARGET_METRICS = ARGS.faucet_target_metrics.split(',')
        GAUGE_VARZ_METRICS = VARZ_COLLECTOR.retry_get_gauge_metrics(GAUGE_TARGET_METRICS)
        VARZ_METRICS_MAP['gauge_metrics'] = report_metrics(GAUGE_VARZ_METRICS)

    json.dumps(VARZ_METRICS_MAP)
