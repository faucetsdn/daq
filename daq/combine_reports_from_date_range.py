import os
import logger 
import sys
import datetime
import re
import json
import functools

import configurator
from gcp import GcpManager
from report import MdTable

LOGGER = logger.get_logger('combine_reports_from_date_range')

def _render_results(results):
    def reduce_labels(sets):
        return sorted(functools.reduce(lambda cur, acc: acc.union(cur), sets, set())) 
    result_label_sets = map(lambda test: set(test.keys()), results['tests'].values())
    result_labels = reduce_labels(result_label_sets)
    tests_table = MdTable(['test'] + result_labels)
    if results['tests']:
        for test, result in results['tests'].items():
            tests_table.add_row([test, *[str(result.get(label, 0)) for label in result_labels]]) 
    else:
        tests_table.add_row(['No results'])

    category_label_sets = map(lambda category: set(category.keys()), results['categories'].values())
    result_labels = reduce_labels(category_label_sets)
    categories_table = MdTable(['categories'] + result_labels)
    if results['categories']:
        for category, result in results['categories'].items():
            categories_table.add_row([category, *[str(result.get(label, 0)) for label in result_labels]]) 
    else:
        categories_table.add_row(['No results'])
    
    missing_table = MdTable(['missing tests', 'count'])
    if results['missing']:
        for test in sorted(results['missing'].keys()):
            missing_table.add_row([test, str(results['missing'][test])]) 
    else:
        missing_table.add_row(['None'])
    
    return "\n%s\n" * 3 % (tests_table.render(), categories_table.render(), missing_table.render())    

def main(device, start=None, end=None, gcp=None, reports_dir=os.path.join('inst', 'reports')):
    aggregate = {'tests': {}, 'categories': {}, 'missing': {}}
    if gcp:
        json_reports = gcp.get_reports_from_date_range(device, start=start, end=end)    
    else: 
        LOGGER.info('Looking for reports locally')
        prog = re.compile('^report_%s_\d{4}-\d{2}-\d{2}T\d{6}\+\d{4}.*\.json$' % device) 
        json_files = [f for f in os.listdir(reports_dir) if prog.match(f)]
        def get_json_reports():
            for json_file in json_files:  
                timestamp = list(json_file.split('_')[-1][:22])
                timestamp[13:13], timestamp[16:16], timestamp[22:22] = list(":" * 3)
                timestamp = datetime.datetime.fromisoformat(''.join(timestamp)).replace(tzinfo=None)
                if (start and timestamp < start) or (end and timestamp > end):
                    LOGGER.info('Skipping file %s' % json_file)
                    continue
                LOGGER.info('Processing file %s' % json_file)
                with open(os.path.join(reports_dir, json_file), 'r') as f:
                    yield json.loads(f.read())
        json_reports = get_json_reports() 
    for json_report in json_reports:
        for test in json_report.get('missing_tests', []):
            if test not in aggregate["missing"]:
                aggregate['missing'][test] = 0
            aggregate['missing'][test] += 1
        for module, module_result in json_report.get('modules', {}).items():
            for test, test_result in module_result.get('tests', {}).items():
                result = test_result.get('result')
                category = test_result.get('category')
                if test not in aggregate['tests']:
                    aggregate['tests'][test] = {}
                if category not in aggregate['categories']:
                    aggregate['categories'][category] = {}
                if result not in aggregate['tests'][test]:
                    aggregate['tests'][test][result] = 0
                if result not in aggregate['categories'][category]:
                    aggregate['categories'][category][result] = 0
                aggregate['tests'][test][result] += 1
                aggregate['categories'][category][result] += 1
    result_str = _render_results(aggregate)
    reports_path = os.path.join(reports_dir, 'combo_%s_(%s,%s).md' % (device, start, end)) 
    with open(reports_path, 'w') as f:
        f.write('# Combined Results\n')
        f.write('Device: %s Start: %s End: %s\n' % (device, start, end))
        f.write(result_str)
    LOGGER.info('Report written to %s' % reports_path)

if __name__ == '__main__':
    logger.set_config(format='%(levelname)s:%(message)s', level="INFO")
    CONFIGURATOR = configurator.Configurator()
    CONFIG = CONFIGURATOR.parse_args(sys.argv)
    GCP = None
    if CONFIG.get('gcp_cred'):
        GCP = GcpManager(CONFIG, None)
    assert all([attr in CONFIG for attr in ('from_time', 'to_time', 'device')]), """
Usage: combine_reports_from_date_range.py device=xxxxxxxxxxxx
       [from_time='YYYY-MM-DDThh:mm:ss']
       [to_time='YYYY-MM-DDThh:mm:ss']
       local/system.yaml"""
    FROM_TIME = datetime.datetime.fromisoformat(CONFIG.get('from_time')).replace(tzinfo=None)
    TO_TIME = datetime.datetime.fromisoformat(CONFIG.get('to_time')).replace(tzinfo=None)
    main(CONFIG.get('device'), start=FROM_TIME, end=TO_TIME, gcp=GCP) 
