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
DEFAULT_REPORTS_DIR = os.path.join('inst', 'reports')


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

    reports_table = MdTable(['reports'])
    for report in sorted(results['reports'].keys()):
        reports_table.add_row([report])

    all_tables = [tests_table, categories_table, missing_table, reports_table]
    return '\n'.join(map(lambda x: x.render(), all_tables))

def _iso_to_fname(timestamp):
    return timestamp.isoformat().replace(':', '') if timestamp else None


def _get_local_reports(device, reports_dir, start, end, count):
    LOGGER.info('Looking for reports locally')
    report_re = re.compile(r'^report_%s_(\d{4}-\d{2}-\d{2}T\d{6})\.json$' % device)
    json_files = [f for f in os.listdir(reports_dir) if report_re.match(f)]
    json_files.sort()
    if count and len(json_files) > count:
        json_files = json_files[len(json_files) - count:]
    for json_file in json_files:
        timestamp = report_re.search(json_file).group(1)
        start_str = _iso_to_fname(start)
        end_str = _iso_to_fname(end)
        if (start_str and timestamp < start_str) or (end_str and timestamp > end_str):
            LOGGER.info('Skipping file %s' % json_file)
            continue
        LOGGER.info('Processing file %s' % json_file)
        with open(os.path.join(reports_dir, json_file), 'r') as json_file_handler:
            yield json.loads(json_file_handler.read())


def main(device, start=None, end=None, gcp=None, reports_dir=DEFAULT_REPORTS_DIR, count=0):
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    """Main script function"""

    device = device.replace(':', '').lower()
    report_source = 'gcp' if gcp else 'local'
    if gcp:
        device_full = ":".join([device[i:i + 2] for i in range(0, len(device), 2)])
        json_reports = gcp.get_reports_from_date_range(device_full, start=start, end=end,
                                                       count=count)
    else:
        json_reports = _get_local_reports(device, reports_dir, start, end, count)

    json_reports = list(json_reports)

    aggregate = {'tests': {}, 'categories': {}, 'missing': {}, 'reports': {}}
    for json_report in json_reports:
        aggregate['reports'][json_report['timestamp']] = True
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
    start_stamp = _iso_to_fname(start)
    end_stamp = _iso_to_fname(end)
    reports_path = os.path.join(reports_dir, 'combo_%s_%s_%s.md' % (device, start_stamp, end_stamp))
    with open(reports_path, 'w') as report_file:
        report_file.write('# Combined Results\n')
        report_file.write('Device: %s\nStart: %s\nEnd: %s\n' % (device, start, end))
        report_file.write('Source: %s\n\n' % report_source)
        report_file.write(result_str)
    LOGGER.info('Report written to %s' % reports_path)
    assert not count or count == len(json_reports), 'Did not find expected %d reports' % count


def _convert_iso(timestamp):
    return datetime.datetime.fromisoformat(timestamp).replace(tzinfo=None) if timestamp else None


if __name__ == '__main__':
    logger.set_config(format='%(levelname)s:%(message)s', level="INFO")
    CONFIGURATOR = configurator.Configurator()
    CONFIG = CONFIGURATOR.parse_args(sys.argv)
    GCP = None
    if CONFIG.get('gcp_cred') and CONFIG.get('from_gcp'):
        GCP = GcpManager(CONFIG, None)
    assert all([attr in CONFIG for attr in ('from_time', 'to_time', 'device')]), """
Combines reports under inst/reports(default) or from GCP
Usage: combine_reports_from_date_range.py
    [local/system.yaml]
    device=xx:xx:xx:xx:xx:xx
    from_time='YYYY-MM-DDThh:mm:ss'
    to_time='YYYY-MM-DDThh:mm:ss'
    [count=N]
    [from_gcp='true']
"""
    FROM_TIME = _convert_iso(CONFIG.get('from_time'))
    TO_TIME = _convert_iso(CONFIG.get('to_time'))
    COUNT = int(CONFIG.get('count', 0))
    main(CONFIG.get('device'), start=FROM_TIME, end=TO_TIME, gcp=GCP, count=COUNT)
