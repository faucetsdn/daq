"""Device report handler"""

import copy
import datetime
import json
import os
import re
import shutil
from enum import Enum

import pytz
import jinja2

import pypandoc
import weasyprint

from env import DAQ_RUN_DIR, DAQ_LIB_DIR
import gcp
import logger
LOGGER = logger.get_logger('report')
REPORT_BASE_DIR = os.path.join(DAQ_RUN_DIR, "reports")

class ResultType(Enum):
    """Enum for all test module info"""
    REPORT_PATH = "report_path"
    MODULE_CONFIG = "module_config"
    MODULE_CONFIG_PATH = "module_config_path"
    RETURN_CODE = "return_code"
    EXCEPTION = "exception"
    ACTIVATION_LOG_PATH = "activation_log_path"

class MdTable():
    """Md table renderer"""

    _DIV = "---"
    _MARK = '|'

    def __init__(self, headers):
        self.headers = ['', *headers, '']
        separators = [self._DIV for _ in headers]
        self._header_separator = self._MARK.join(['', *separators, ''])
        self.rows = []

    def add_row(self, row):
        """Add one row to the md table"""
        self.rows.append(['', *map(str.strip, row), ''])

    def render(self):
        """returns a string for md"""
        table_str = '%s\n%s\n' % (self._MARK.join(self.headers), self._header_separator)
        return table_str + '\n'.join([self._MARK.join(row) for row in self.rows]) + '\n'

class ReportGenerator:
    """Generate a report for device qualification"""

    _NAME_FORMAT = "report_%s_%s"
    _SIMPLE_REPORT = "report"
    _REPORT_CSS_PATH = os.path.join(DAQ_LIB_DIR, 'resources', 'setups', 'baseline',
                                    'device_report.css')
    _REPORT_TMP_HTML_PATH = os.path.join(DAQ_RUN_DIR, 'last_report_out.html')
    _TEST_SEPARATOR = "\n## %s\n"
    _TEST_SUBHEADER = "\n#### %s\n"
    _RESULT_REGEX = r'^RESULT (.*?)\s+(.*?)\s+([^%]*)\s*(%%.*)?$'
    _SUMMARY_LINE = "Report summary"
    _REPORT_COMPLETE = "Report complete"
    _DEFAULT_HEADER = "# DAQ scan report for device %s"
    _REPORT_TEMPLATE = "report_template.md"
    _PATH_PREFIX = "report_path"
    _DEFAULT_CATEGORY = 'Other'
    _DEFAULT_EXPECTED = 'Other'
    _PRE_START_MARKER = "```"
    _PRE_END_MARKER = "```"
    _CATEGORY_BASE_COLS = ["Category", "Total Tests", "Result"]
    _EXPECTED_HEADER = "Expectation"
    _SUMMARY_HEADERS = ["Result", "Test", "Category", "Expectation", "Notes"]
    _MISSING_TEST_RESULT = 'gone'
    _NO_REQUIRED = 'n/a'
    _PASS_REQUIRED = 'PASS'

    _INDEX_PASS = 0
    _INDEX_FAIL = 1
    _INDEX_SKIP = 2

    # pylint: disable=too-many-arguments
    def __init__(self, config, target_mac, module_config, report_sink, dev_base):
        self._config = config
        self._report_sink = report_sink
        self._module_config = copy.deepcopy(module_config)
        self._repitems = {}
        self._clean_mac = target_mac.replace(':', '')
        self._finalized = False
        self._start_time = datetime.datetime.now(pytz.utc).replace(microsecond=0)
        report_mark = self._start_time.isoformat().replace(':', '').replace('+0000', '')
        self._report_name = self._NAME_FORMAT % (self._clean_mac, report_mark)
        if not os.path.isdir(REPORT_BASE_DIR):
            os.makedirs(REPORT_BASE_DIR)
        self._report_prefix = os.path.join(REPORT_BASE_DIR, self._report_name)
        LOGGER.info('Writing report to %s.*', self._report_prefix)

        out_base = config.get('site_path', DAQ_RUN_DIR)
        out_path = os.path.join(out_base, 'mac_addrs', self._clean_mac)
        alt_path = out_path if os.path.isdir(out_path) else None
        self._alt_prefix = os.path.join(alt_path, self._SIMPLE_REPORT) if alt_path else None
        LOGGER.info('Writing alternate report to %s.*', self._alt_prefix)

        self._dev_prefix = os.path.join(dev_base, self._report_name) if dev_base else None
        LOGGER.info('Writing device report to %s.*', self._dev_prefix)

        self._all_results = None
        self._result_headers = list(self._module_config.get('report', {}).get('results', []))
        self._results = {}
        self._expected_headers = list(self._module_config.get('report', {}).get('expected', []))
        self._expecteds = {}
        self._categories = list(self._module_config.get('report', {}).get('categories', []))
        self._category_headers = []
        self._append_notices = []
        self._file_md = None

    def _write(self, msg=''):
        self._file_md.write(msg)

    def _writeln(self, msg=''):
        self._write(msg + '\n')

    def _append_file(self, input_path, add_pre=True):
        LOGGER.info('Copying test report %s', input_path)
        if add_pre:
            self._writeln(self._PRE_START_MARKER)
        with open(input_path, 'r') as input_stream:
            shutil.copyfileobj(input_stream, self._file_md)
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
        LOGGER.info('Finalizing %s', self._report_name)
        assert not self._finalized, 'report already finalized'
        self._finalized = True
        self._module_config['clean_mac'] = self._clean_mac
        self._module_config['start_time'] = self._start_time
        self._module_config['end_time'] = datetime.datetime.now(pytz.utc).replace(microsecond=0)
        self._process_results()
        self._write_md_report()
        self._write_pdf_report()
        self._write_json_report()
        self._report_sink(self._all_results)
        LOGGER.info('Copying reports to %s.*', self._alt_prefix)
        LOGGER.info('Copying reports to %s.*', self._dev_prefix)
        report_paths = {}
        for extension in ['.md', '.pdf', '.json']:
            report_path = self._report_prefix + extension
            if self._alt_prefix:
                shutil.copyfile(report_path, self._alt_prefix + extension)
            if self._dev_prefix:
                shutil.copyfile(report_path, self._dev_prefix + extension)
            report_paths.update({self._PATH_PREFIX + extension: report_path})
        return report_paths, self._all_results

    def _write_json_report(self):
        json_path = self._report_prefix + '.json'
        with open(json_path, 'w') as json_file:
            json.dump(self._all_results, json_file)

    def _process_results(self):
        self._all_results = {"modules": {}}
        for (module_name, result_dict) in self._repitems.items():
            module_result = {"tests": {}}
            self._all_results["modules"][module_name] = module_result
            for result_type in ResultType:
                if result_type in result_dict:
                    module_result[result_type.value] = result_dict[result_type]
            if ResultType.REPORT_PATH not in result_dict:
                continue
            path = result_dict[ResultType.REPORT_PATH]
            with open(path) as stream:
                for line in stream:
                    match = re.search(self._RESULT_REGEX, line)
                    if match:
                        result, test_name, extra = match.group(1), match.group(2), match.group(3)
                        self._accumulate_result(test_name, result, extra, module_name=module_name)
                        module_result["tests"][test_name] = self._results[test_name]
        self._all_results['timestamp'] = gcp.get_timestamp()
        self._all_results['missing_tests'] = self._find_missing_test_results()

    def _write_md_report(self):
        """Generate the markdown report to be copied into /inst and /local"""
        with open(self._report_prefix + '.md', "w") as md_file:
            self._file_md = md_file
            self._append_report_header()
            self._write_test_summary()
            self._write_repitems()
            self._writeln(self._TEST_SEPARATOR % self._REPORT_COMPLETE)
            self._file_md = None

    def _write_pdf_report(self):
        """Convert the markdown report to html, then pdf"""
        LOGGER.info('Generating HTML for writing pdf report...')
        md_file = self._report_prefix + '.md'
        pypandoc.convert_file(md_file, 'html',
                              outputfile=self._REPORT_TMP_HTML_PATH,
                              extra_args=['-V', 'geometry:margin=1.5cm', '--columns', '1000'])
        LOGGER.info('Metamorphosising HTML to PDF...')
        html_writer = weasyprint.HTML(self._REPORT_TMP_HTML_PATH)
        pdf_file = self._report_prefix + '.pdf'
        html_writer.write_pdf(pdf_file, stylesheets=[weasyprint.CSS(self._REPORT_CSS_PATH)])

    def _write_test_summary(self):
        self._writeln(self._TEST_SEPARATOR % self._SUMMARY_LINE)
        self._analyse_and_write_results()
        self._write_test_tables()

    def _accumulate_result(self, test_name, result, extra='', module_name=None):
        assert test_name not in self._results, 'result already exists: ' % test_name

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
        self._results[test_name] = {
            "result": result,
            "test_name": test_name,
            "module_name": module_name,
            "category": category_name,
            "expected": expected_name,
            "result_description": extra
        }

    def _write_test_tables(self):
        self._write_category_table()
        self._writeln()
        self._write_expected_table()
        self._writeln()
        self._write_result_table()
        self._writeln()

    def _analyse_and_write_results(self):
        """ Analyse the test results to determine if the device is a pass or fail
            and identify possible issues (e.g. gone) and writes these to the report
        """
        passes = True
        gone = False

        # Analyse results
        for test_name, result_dict in self._results.items():
            test_info = self._get_test_info(test_name)

            if 'required' in test_info:
                required_result = test_info['required']

                # The device overall fails if any result is unexpected
                if result_dict["result"] != required_result:
                    passes = False

                if result_dict["result"] == 'gone':
                    gone = True

        # Write Results
        self._writeln('Overall device result %s' % ('PASS' if passes else 'FAIL'))
        self._writeln()

        if gone:
            gone_message = ('**Some tests report as GONE. '
                            'Please check for possible misconfiguration**')
            self._writeln(gone_message)
            self._writeln()

    def _join_category_results(self, results):
        """ Used to convert list of results into the pass/fail/skip format
            for category table

        Args:
        results: List of results

        Returns:
        String in pass/fail/skip format
        """
        return '/'.join(str(value) for value in results)

    def _write_category_table(self):
        """ Write the first category and expected table
        """

        rows = []
        self._category_headers = self._CATEGORY_BASE_COLS + self._expected_headers

        for category in self._categories:
            total = 0

            results = [[0, 0, 0] for _ in range(len(self._expected_headers))]
            result = self._NO_REQUIRED  # Overall category result

            for test_name, result_dict in self._results.items():
                test_info = self._get_test_info(test_name)
                category_name = test_info.get('category', self._DEFAULT_CATEGORY)

                # all tests must have required in order to be counted
                if category_name == category and 'required' in test_info:
                    total += 1

                    expected_name = test_info.get('expected', self._DEFAULT_EXPECTED)
                    expected_index = self._expected_headers.index(expected_name)

                    # Put test results into right location in the result matrix
                    if result_dict["result"] in ("pass", "info"):
                        results[expected_index][self._INDEX_PASS] += 1
                    elif result_dict["result"] == "skip":
                        results[expected_index][self._INDEX_SKIP] += 1
                    else:
                        results[expected_index][self._INDEX_FAIL] += 1

                    # Calculate overall rolling result for the category
                    if result not in (result_dict["result"], self._NO_REQUIRED):
                        # Consider info and pass alike
                        # TODO remove when info tests are removed
                        if result_dict["result"] == 'info':
                            result_dict["result"] = 'pass'
                        else:
                            result = "fail"
                    else:
                        result = result_dict["result"]

            results = list(map(self._join_category_results, results))

            row = [category, str(total), result.upper()] + results
            rows.append(row)

        table = MdTable(self._category_headers)
        for row in rows:
            table.add_row(row)
        self._write(table.render())
        self._writeln('Syntax: Pass / Fail / Skip')

    def _write_expected_table(self):
        table = MdTable([self._EXPECTED_HEADER, *self._result_headers])
        for exp_name in self._expected_headers:
            table_row = [exp_name]
            for result in self._result_headers:
                expected = self._expecteds.get(exp_name, {})
                table_row.append(str(expected.get(result, 0)))
            table.add_row(table_row)
        self._write(table.render())

    def _write_result_table(self):
        table = MdTable(self._SUMMARY_HEADERS)
        for _, result in sorted(self._results.items()):
            table.add_row([result["result"], result["test_name"], result["category"],\
                    result["expected"], result["result_description"]])
        self._write(table.render())

    def _find_missing_test_results(self):
        missing = []
        if 'tests' in self._module_config:
            for test_name in self._module_config['tests'].keys():
                test_info = self._get_test_info(test_name)
                if test_info.get('required') and test_name not in self._results:
                    self._accumulate_result(test_name, self._MISSING_TEST_RESULT)
                    missing.append(test_name)
        return missing

    def _get_test_info(self, test_name):
        return self._module_config.get('tests', {}).get(test_name, {})

    def _write_repitems(self):
        from host import get_test_config  # Deferring import
        for (test_name, result_dict) in self._repitems.items():
            # To not write a module header if there is nothing to report
            def writeln(line, test_name=test_name):
                if not writeln.results:
                    writeln.results = True
                    self._writeln(self._TEST_SEPARATOR % ("Module " + test_name))
                self._writeln(line)
            writeln.results = False
            if ResultType.REPORT_PATH in result_dict:
                writeln(self._TEST_SUBHEADER % "Report")
                self._append_file(result_dict[ResultType.REPORT_PATH])
            if ResultType.MODULE_CONFIG in result_dict:
                module_configs = result_dict[ResultType.MODULE_CONFIG]
                config = get_test_config(module_configs, test_name)
                if config and len(config) > 0:
                    writeln(self._TEST_SUBHEADER % "Module Config")
                    table = MdTable(["Attribute", "Value"])
                    for key, value in config.items():
                        table.add_row((key, str(value)))
                    self._write(table.render())
            if result_dict.get(ResultType.EXCEPTION):
                writeln(self._TEST_SUBHEADER % "Exceptions")
                writeln(result_dict[ResultType.EXCEPTION])

    def accumulate(self, test_name, result_dict):
        """Accumulate test reports into the overall device report"""
        valid_result_types = all(isinstance(key, ResultType) for key in result_dict)
        assert valid_result_types, "Unknown result type in %s" % result_dict
        self._repitems.setdefault(test_name, {}).update(result_dict)
