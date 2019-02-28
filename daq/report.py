"""Device report handler"""

import datetime
import logging
import os
import pytz
import shutil
import time

LOGGER = logging.getLogger('report')

class ReportGenerator():
    """Generate a report for device qualification"""

    _NAME_FORMAT = "report_%s_%s.txt"

    def __init__(self, report_base, dev_base, target_mac):
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
        self.write('DAQ scan report for device %s' % self._clean_mac)
        self.write('Started %s' % report_when)
        dev_path = os.path.join(str(dev_base), self._clean_mac, 'report_description.txt')
        if os.path.isfile(dev_path):
            self.write('')
            self.copy(dev_path)
        else:
            LOGGER.info('Device description not found in %s', dev_path)

    def write(self, msg):
        """Write a message to a report file"""
        self._file.write(msg + '\n')
        self._file.flush()

    def copy(self, input_path):
        """Copy an input file to the report"""
        LOGGER.info('Copying %s to report', input_path)
        with open(input_path, 'r') as input_stream:
            shutil.copyfileobj(input_stream, self._file)
        self._file.flush()

    def finalize(self):
        LOGGER.info('Finalizing report %s', self.path)
        self.write('Report complete.')
        self._file.close()
        self._file = None
