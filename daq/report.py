"""Device report handler"""

import datetime
import logging
import os
import re
import shutil

import pytz

LOGGER = logging.getLogger('report')

class ReportGenerator():
    """Generate a report for device qualification"""

    _NAME_FORMAT = "report_%s_%s.txt"
    _SIMPLE_FORMAT = "device_report.md"
    _TEST_SEPARATOR = "\n## %s\n"
    _RESULT_REGEX = r'^RESULT (.*?)\s*(#.*)?$'
    _SUMMARY_LINE = "Report summary"
    _REPORT_COMPLETE = "Report complete"
    _REPORT_HEADER = "# DAQ scan report for device %s"
    _PRE_START_MARKER = "```"
    _PRE_END_MARKER = "```"

    def __init__(self, config, tmp_base, target_mac):
        self._reports = []
        self._clean_mac = target_mac.replace(':', '')
        report_when = datetime.datetime.now(pytz.utc).replace(microsecond=0)
        report_filename = self._NAME_FORMAT % (self._clean_mac,
                                               report_when.isoformat().replace(':', ''))
        self._filename = report_filename
        report_base = os.path.join(tmp_base, 'reports')
        if not os.path.isdir(report_base):
            os.makedirs(report_base)
        report_path = os.path.join(report_base, report_filename)
        LOGGER.info('Creating report as %s', report_path)
        self.path = report_path
        self._file = open(report_path, "w")
        self._writeln(self._REPORT_HEADER % self._clean_mac)
        self._writeln('Started %s' % report_when)

        dev_base = config.get('site_path', tmp_base)
        dev_path = os.path.join(dev_base, 'mac_addrs', self._clean_mac, 'report_description.txt')
        if os.path.isfile(dev_path):
            self._writeln('')
            self._append_file(dev_path, add_pre=False)
        else:
            LOGGER.info('Device description %s not found', dev_path)

        out_base = config.get('site_report', dev_base)
        out_path = os.path.join(out_base, 'mac_addrs', self._clean_mac)
        if os.path.isdir(out_path):
            self._alt_path = os.path.join(out_path, self._SIMPLE_FORMAT)
        else:
            LOGGER.info('Device report path %s not found', out_path)
            self._alt_path = None

    def _writeln(self, msg):
        self._file.write(msg + '\n')
        self._file.flush()

    def _append_file(self, input_path, add_pre=True):
        LOGGER.info('Copying test report %s', input_path)
        if add_pre:
            self._writeln(self._PRE_START_MARKER)
        with open(input_path, 'r') as input_stream:
            shutil.copyfileobj(input_stream, self._file)
        if add_pre:
            self._writeln(self._PRE_END_MARKER)

    def finalize(self):
        """Finalize this report"""
        LOGGER.info('Finalizing report %s', self._filename)
        self._write_test_summary()
        self._copy_test_reports()
        self._writeln(self._TEST_SEPARATOR % self._REPORT_COMPLETE)
        self._file.close()
        self._file = None
        if self._alt_path:
            LOGGER.info('Copying report to %s', self._alt_path)
            shutil.copyfile(self.path, self._alt_path)

    def _write_test_summary(self):
        self._writeln(self._TEST_SEPARATOR % self._SUMMARY_LINE)
        for (_, path) in self._reports:
            with open(path) as stream:
                for line in stream:
                    match = re.search(self._RESULT_REGEX, line)
                    if match:
                        self._writeln(match.group(1))

    def _copy_test_reports(self):
        for (name, path) in self._reports:
            self._writeln(self._TEST_SEPARATOR % ("Module " + name))
            self._append_file(path)

    def accumulate(self, test_name, report_path):
        """Accumulate a test report into the overall device report"""
        self._reports.append((test_name, report_path))
