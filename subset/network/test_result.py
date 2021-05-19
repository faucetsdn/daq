""" Wrapper to build test result output
"""
from dataclasses import dataclass

PASS = 'pass'
SKIP = 'skip'
FAIL = 'fail'


@dataclass
class test_result:
    _dash_break_line = '--------------------\n'

    name: str
    description: str
    summary: str = ''
    result: str = 'fail'

    def write_results(self, report_filename):
        """Writes result to file

        Args:
            report_filename: path to file to write results to
        """
        with open(report_filename, 'a+') as file_open:
            file_open.write("{b}{t}\n{b}".format(b=self._dash_break_line, t=self.name))
            file_open.write("{d}\n{b}".format(
                b=self._dash_break_line, d=self.description))
            file_open.write("RESULT {r} {t} {s}\n".format(
                r=self.result, t=self.name, s=self.summary.strip()))

    def add_summary(self, text):
        """Adds summary text to result.

        e.g. RESULT pass test.name <SUMMARY TEXT>
        Appends to existing text with a space if any.

        Args:
            Text to add.
        """
        self.summary = self.summary + " " + text if self.summary else text
