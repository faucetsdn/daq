"""Script for combining reports"""
import os
import sys
import datetime
import re
import json
import functools

import logger
import configurator
from gcp import GcpManager
from report import MdTable

LOGGER = logger.get_logger('combine_reports_from_date_range')


def _reduce_labels(sets):
    return sorted(functools.reduce(lambda cur, acc: acc.union(cur), sets, set()))

def _render_results(results):
    result_label_sets = map(lambda test: set(test.keys()), results['tests'].values())
    result_labels = _reduce_labels(result_label_sets)
    tests_table = MdTable(['test'] + result_labels)
    if results['tests']:
        for test, result in results['tests'].items():
            tests_table.add_row([test, *[str(result.get(label, 0)) for label in result_labels]])
    else:
        tests_table.add_row(['No results'])

    category_label_sets = map(lambda category: set(category.keys()), results['categories'].values())
    result_labels = _reduce_labels(category_label_sets)
    categories_table = MdTable(['categories'] + result_labels)
    if results['categories']:
        for category, result in results['categories'].items():
            row_result = [str(result.get(label, 0)) for label in result_labels]
            categories_table.add_row([category, *row_result])
    else:
        categories_table.add_row(['No results'])

    missing_table = MdTable(['missing tests', 'count'])
    if results['missing']:
        for test in sorted(results['missing'].keys()):
            missing_table.add_row([test, str(results['missing'][test])])
    else:
        missing_table.add_row(['None'])

    return "\n%s\n" * 3 % (tests_table.render(), categories_table.render(), missing_table.render())

def _get_local_reports(device, reports_dir, start, end):
    LOGGER.info('Looking for reports locally')
    report_re = re.compile(r'^report_%s_\d{4}-\d{2}-\d{2}T\d{6}\+\d{4}.*\.json$' % device)
    ts_re = re.compile(r'\d{4}-\d{2}-\d{2}T\d{6}\+\d{4}')
    json_files = [f for f in os.listdir(reports_dir) if report_re.match(f)]
    for json_file in json_files:
        timestamp = ts_re.search(json_file).group(0)
        start_str = start.isoformat().replace(':', '') if start else None
        end_str = end.isoformat().replace(':', '') if end else None
        if (start_str and timestamp < start_str) or (end_str and timestamp > end_str):
            LOGGER.info('Skipping file %s' % json_file)
            continue
        LOGGER.info('Processing file %s' % json_file)
        with open(os.path.join(reports_dir, json_file), 'r') as json_file_handler:
            yield json.loads(json_file_handler.read())

def main(device, start=None, end=None, gcp=None, reports_dir=os.path.join('inst', 'reports')):
    # pylint: disable=too-many-locals
    """Main script function"""
    aggregate = {'tests': {}, 'categories': {}, 'missing': {}}
    device = device.replace(':', '').lower()
    if gcp:
        device_full = ":".join([device[i:i + 2] for i in range(0, len(device), 2)])
        json_reports = gcp.get_reports_from_date_range(device_full, start=start, end=end)
    else:
        json_reports = _get_local_reports(device, reports_dir, start, end)

    for json_report in json_reports:
        for test in json_report.get('missing_tests', []):
            aggregate['missing'].setdefault(test, 0)
            aggregate['missing'][test] += 1
        for _, module_result in json_report.get('modules', {}).items():
            for test, test_result in module_result.get('tests', {}).items():
                result = test_result.get('result')
                category = test_result.get('category')
                aggregate['tests'].setdefault(test, {})
                aggregate['tests'][test].setdefault(result, 0)
                aggregate['categories'].setdefault(category, {})
                aggregate['categories'][category].setdefault(result, 0)
                aggregate['tests'][test][result] += 1
                aggregate['categories'][category][result] += 1
    result_str = _render_results(aggregate)
    reports_path = os.path.join(reports_dir, 'combo_%s_(%s,%s).md' % (device, start, end))
    with open(reports_path, 'w') as report_file:
        report_file.write('# Combined Results\n')
        report_file.write('Device: %s Start: %s End: %s\n' % (device, start, end))
        report_file.write(result_str)
    LOGGER.info('Report written to %s' % reports_path)


if __name__ == '__main__':
    logger.set_config(format='%(levelname)s:%(message)s', level="INFO")
    CONFIGURATOR = configurator.Configurator()
    CONFIG = CONFIGURATOR.parse_args(sys.argv)
    GCP = None
    if CONFIG.get('gcp_cred') and CONFIG.get('use_gcp'):
        GCP = GcpManager(CONFIG, None)
    assert all([attr in CONFIG for attr in ('from_time', 'to_time', 'device')]), """
Usage: combine_reports_from_date_range.py device=xx:xx:xx:xx:xx:xx
       [from_time='YYYY-MM-DDThh:mm:ss']
       [to_time='YYYY-MM-DDThh:mm:ss']
       [use_gcp='true']
       local/system.yaml"""
    FROM_TIME = datetime.datetime.fromisoformat(CONFIG.get('from_time')).replace(tzinfo=None)
    TO_TIME = datetime.datetime.fromisoformat(CONFIG.get('to_time')).replace(tzinfo=None)
    main(CONFIG.get('device'), start=FROM_TIME, end=TO_TIME, gcp=GCP)
