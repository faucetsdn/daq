"""Dummy ipaddr accompanying docker module"""

from __future__ import absolute_import
import sys

TEST_REQUEST = str(sys.argv[1])


def main():
    """main"""
    ipaddr_log = '/tmp/activate.log'
    report_filename = 'report.txt'
    dash_break_line = '--------------------\n'
    description_dhcp_short = 'Reconnect device and check for DHCP request.'
    description_dhcp_long = 'Wait for lease expiry and check for DHCP request.'
    result = None

    def _write_report(string_to_append):
        with open(report_filename, 'a+') as file_open:
            file_open.write(string_to_append)

    def _test_dhcp_short():
        return 'fail'

    def _test_dhcp_long():
        return 'fail'

    _write_report("{b}{t}\n{b}".format(b=dash_break_line, t=TEST_REQUEST))
    summary = ""
    with open(ipaddr_log, 'r') as fd:
        summary = fd.read()
    if TEST_REQUEST == 'connection.network.dhcp_short':
        _write_report("{d}\n{b} \n {s}".format(b=dash_break_line, d=description_dhcp_short,
                                               s=summary))
        result = _test_dhcp_short()

    elif TEST_REQUEST == 'connection.network.dhcp_long':
        _write_report("{d}\n{b}".format(b=dash_break_line, d=description_dhcp_long))
        result = _test_dhcp_long()

    _write_report("RESULT {r} {t} \n".format(r=result, t=TEST_REQUEST))


if __name__ == "__main__":
    main()
