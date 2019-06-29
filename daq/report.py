"""Device report handler"""

import copy
import datetime
import logging
import os
import re
import shutil

import jinja2
import pytz

LOGGER = logging.getLogger('report')


class ReportGenerator:
    """Generate a report for device qualification"""

    _NAME_FORMAT = "report_%s_%s.md"
    _SIMPLE_FORMAT = "device_report.md"
    _TEST_SEPARATOR = "\n## %s\n"
    _RESULT_REGEX = r'^RESULT (.*?)\s+(.*?)\s+([^%]*)\s*(%%.*)?$'
    _SUMMARY_LINE = "Report summary"
    _REPORT_COMPLETE = "Report complete"
    _DEFAULT_HEADER = "# DAQ scan report for device %s"
    _REPORT_TEMPLATE = "report_template.md"
    _DEFAULT_CATEGORY = 'Other'
    _DEFAULT_EXPECTED = 'Other'
    _PRE_START_MARKER = "```"
    _PRE_END_MARKER = "```"
    _TABLE_DIV = "---"
    _TABLE_MARK = '|'
    _CATEGORY_HEADERS = ["Category", "Result"]
    _EXPECTED_HEADER = "Expectation"
    _SUMMARY_HEADERS = ["Result", "Test", "Category", "Expectation", "Notes"]
    _MISSING_TEST_RESULT = 'gone'
    _NO_REQUIRED = 'n/a'
    _PASS_REQUIRED = 'PASS'

    def __init__(self, config, tmp_base, target_mac, module_config):
        self._config = config
        self._module_config = copy.deepcopy(module_config)
        self._reports = []
        self._clean_mac = target_mac.replace(':', '')
        report_when = datetime.datetime.now(pytz.utc).replace(microsecond=0)
        report_filename = self._NAME_FORMAT % (self._clean_mac,
                                               report_when.isoformat().replace(':', ''))
        self._start_time = report_when
        self._filename = report_filename
        report_base = os.path.join(tmp_base, 'reports')
        if not os.path.isdir(report_base):
            os.makedirs(report_base)
        report_path = os.path.join(report_base, report_filename)
        LOGGER.info('Creating report as %s', report_path)
        self.path = report_path
        self._file = None

        out_base = config.get('site_path', tmp_base)
        out_path = os.path.join(out_base, 'mac_addrs', self._clean_mac)
        if os.path.isdir(out_path):
            self._alt_path = os.path.join(out_path, self._SIMPLE_FORMAT)
        else:
            LOGGER.info('Device report path %s not found', out_path)
            self._alt_path = None

        self._result_headers = list(self._module_config.get('report', {}).get('results', []))
        self._results = {}
        self._expected_headers = list(self._module_config.get('report', {}).get('expected', []))
        self._expecteds = {}
        self._categories = list(self._module_config.get('report', {}).get('categories', []))

    def _writeln(self, msg=''):
        self._file.write(msg + '\n')

    def _append_file(self, input_path, add_pre=True):
        LOGGER.info('Copying test report %s', input_path)
        if add_pre:
            self._writeln(self._PRE_START_MARKER)
        with open(input_path, 'r') as input_stream:
            shutil.copyfileobj(input_stream, self._file)
        if add_pre:
            self._writeln(self._PRE_END_MARKER)

    def _append_report_header(self):
        template_file = os.path.join(self._config.get('site_path'), self._REPORT_TEMPLATE)
        if not os.path.exists(template_file):
            LOGGER.info('Skipping missing report header template %s', template_file)
            self._writeln(self._DEFAULT_HEADER % self._clean_mac)
            return
        LOGGER.info('Adding templated report header from %s', template_file)
        try:
            undefined_logger = jinja2.make_logging_undefined(logger=LOGGER, base=jinja2.Undefined)
            environment = jinja2.Environment(loader=jinja2.FileSystemLoader('.'),
                                             undefined=undefined_logger)
            self._writeln(environment.get_template(template_file).render(self._module_config))
        except Exception as e:
            self._writeln('Report generation error: %s' % e)
            self._writeln('Failing data model:\n%s' % str(self._module_config))
            LOGGER.error('Report generation failed: %s', e)

    def finalize(self):
        """Finalize this report"""
        LOGGER.info('Finalizing report %s', self._filename)
        self._module_config['clean_mac'] = self._clean_mac
        self._module_config['start_time'] = self._start_time
        self._module_config['end_time'] = datetime.datetime.now(pytz.utc).replace(microsecond=0)
        self._file = open(self.path, "w")
        self._append_report_header()
        self._write_test_summary()
        self._copy_test_reports()
        self._writeln(self._TEST_SEPARATOR % self._REPORT_COMPLETE)
        self._file.close()
        self._file = None
        if self._alt_path:
            LOGGER.info('Copying report to %s', self._alt_path)
            shutil.copyfile(self.path, self._alt_path)

    def _write_table(self, items):
        stripped_items = map(str.strip, items)
        self._writeln(self._TABLE_MARK + self._TABLE_MARK.join(stripped_items) + self._TABLE_MARK)

    def _write_test_summary(self):
        self._writeln(self._TEST_SEPARATOR % self._SUMMARY_LINE)
        for (_, path) in self._reports:
            with open(path) as stream:
                for line in stream:
                    match = re.search(self._RESULT_REGEX, line)
                    if match:
                        self._accumulate_test(match.group(2), match.group(1), match.group(3))
        self._finalize_test_info()
        self._write_test_tables()

    def _accumulate_test(self, test_name, result, extra=''):
        if result not in self._result_headers:
            self._result_headers.append(result)
        test_info = self._get_test_info(test_name)

        category_name = test_info.get('category', self._DEFAULT_CATEGORY)
        if category_name not in self._categories:
            self._categories.append(category_name)

        expected_name = test_info.get('expected', self._DEFAULT_EXPECTED)
        if expected_name not in self._expected_headers:
            self._expected_headers.append(expected_name)
        if expected_name not in self._expecteds:
            self._expecteds[expected_name] = {}
        expected = self._expecteds[expected_name]
        if result not in expected:
            expected[result] = 0
        expected[result] += 1
        self._results[test_name] = [result, test_name, category_name, expected_name, extra]

    def _write_test_tables(self):
        self._write_category_table()
        self._writeln()
        self._write_expected_table()
        self._writeln()
        self._write_result_table()
        self._writeln()

    def _write_category_table(self):
        passes = True
        rows = []
        for category in self._categories:
            total = 0
            match = 0
            for test_name in self._results:
                test_info = self._get_test_info(test_name)
                category_name = test_info.get('category', self._DEFAULT_CATEGORY)
                if category_name == category and 'required' in test_info:
                    required_result = test_info['required']
                    total += 1
                    if self._results[test_name][0] == required_result:
                        match += 1
                    else:
                        passes = False

            output = self._NO_REQUIRED if total == 0 else (self._PASS_REQUIRED \
                     if match == total else '%s/%s' % (match, total))
            rows.append([category, output])

        self._writeln('Overall device result %s' % ('PASS' if passes else 'FAIL'))
        self._writeln()
        self._write_table(self._CATEGORY_HEADERS)
        self._write_table([self._TABLE_DIV] * len(self._CATEGORY_HEADERS))
        for row in rows:
            self._write_table(row)

    def _write_expected_table(self):
        self._write_table([self._EXPECTED_HEADER] + self._result_headers)
        self._write_table([self._TABLE_DIV] * (1 + len(self._result_headers)))
        for exp_name in self._expected_headers:
            table_row = [exp_name]
            for result in self._result_headers:
                expected = self._expecteds.get(exp_name, {})
                table_row.append(str(expected.get(result, 0)))
            self._write_table(table_row)

    def _write_result_table(self):
        self._write_table(self._SUMMARY_HEADERS)
        self._write_table([self._TABLE_DIV] * len(self._SUMMARY_HEADERS))
        for match in sorted(self._results.keys()):
            self._write_table(self._results[match])

    def _finalize_test_info(self):
        if 'tests' not in self._module_config:
            return
        for test_name in self._module_config['tests'].keys():
            test_info = self._get_test_info(test_name)
            category_name = test_info.get('category', self._DEFAULT_CATEGORY)
            if not category_name in self._categories:
                self._categories.append(category_name)
            if test_info.get('required'):
                if test_name not in self._results:
                    self._accumulate_test(test_name, self._MISSING_TEST_RESULT)

    def _get_test_info(self, test_name):
        if 'tests' not in self._module_config:
            return {}
        return self._module_config['tests'].get(test_name, {})

    def _copy_test_reports(self):
        for (name, path) in self._reports:
            self._writeln(self._TEST_SEPARATOR % ("Module " + name))
            self._append_file(path)

    def accumulate(self, test_name, test_path):
        """Accumulate a test report into the overall device report"""
        self._reports.append((test_name, test_path))
