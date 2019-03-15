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
    _TEST_SEPARATOR = "\n=============== %s\n"
    _RESULT_REGEX = r'^RESULT (.*?)\s*(#.*)?$'
    _SUMMARY_LINE = "Report summary"
    _REPORT_COMPLETE = "Report complete"

    def __init__(self, report_base, dev_base, target_mac):
        self._reports = []
        self._clean_mac = target_mac.replace(':', '')
        report_when = datetime.datetime.now(pytz.utc).replace(microsecond=0)
        report_filename = self._NAME_FORMAT % (self._clean_mac,
                                               report_when.isoformat().replace(':', ''))
        report_path = os.path.join(report_base, report_filename)
        LOGGER.info('Creating report as %s', report_path)
        self.path = report_path
        if not os.path.isdir(report_base):
            os.makedirs(report_base)
        self._file = open(report_path, "w")
        self._writeln('DAQ scan report for device %s' % self._clean_mac)
        self._writeln('Started %s' % report_when)
        dev_path = os.path.join(str(dev_base), self._clean_mac, 'report_description.txt')
        if os.path.isfile(dev_path):
            self._writeln('')
            self._copy(dev_path)
        else:
            LOGGER.info('Device description not found in %s', dev_path)

    def _writeln(self, msg):
        self._file.write(msg + '\n')
        self._file.flush()

    def _copy(self, input_path):
        LOGGER.info('Copying %s to report', input_path)
        with open(input_path, 'r') as input_stream:
            shutil.copyfileobj(input_stream, self._file)
        self._file.flush()

    def finalize(self):
        """Finalize this report"""
        LOGGER.info('Finalizing report %s', self.path)
        self._write_test_summary()
        self._copy_test_reports()
        self._writeln(self._TEST_SEPARATOR % self._REPORT_COMPLETE)
        self._file.close()
        self._file = None

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
            self._copy(path)

    def accumulate(self, test_name, report_path):
        """Accumulate a test report into the overall device report"""
        self._reports.append((test_name, report_path))
