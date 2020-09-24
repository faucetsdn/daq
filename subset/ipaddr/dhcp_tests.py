from __future__ import absolute_import
import sys

TEST_REQUEST = str(sys.argv[1])
DHCP_REQUEST = 3
DHCP_ACKNOWLEDGE = 5

def main():
    """main"""
    ipaddr_log = '/tmp/activate.log'
    report_filename = 'report.txt'
    dash_break_line = '--------------------\n'
    description_dhcp_short = 'Reconnect device and check for DHCP request.'
    description_dhcp_long = 'Wait for lease expiry and check for DHCP request.'
    running_port_toggle = 'Running dhcp port_toggle test'
    running_dhcp_long = 'Running dhcp long_wait test'
    ip_notification = 'ip notification'
    result = None
    summary = None

    def _write_report(string_to_append):
        with open(report_filename, 'a+') as file_open:
            file_open.write(string_to_append)

    def _get_dhcp_type(capture, dhcp_type, after=None):
        for packet in capture:
            if DHCP not in packet:
                continue
            if packet[DHCP].options[0][1] == dhcp_type:
                if after is None:
                    return packet
                if packet.time > after:
                    return packet
        return None

    def _get_dhcp_option(packet, option):
        for opt in packet[DHCP].options:
            if opt[0] == option:
                return opt[1]
        return None

    def _test_dhcp_short():
        fd = open(ipaddr_log, 'r')
        run_dhcp_short = False
        for line in fd:
            if run_dhcp_short:
                if ip_notification in line:
                    fd.close()
                    return 'pass', 'DHCP request received.'
            if running_port_toggle in line:
                run_dhcp_short = True
        fd.close()
        return 'fail', 'No DHCP request received.'

    def _test_dhcp_long():
        fd = open(ipaddr_log, 'r')
        run_dhcp_long = False
        for line in fd:
            if run_dhcp_long:
                if ip_notification in line:
                    fd.close()
                    return 'pass', 'DHCP request received after lease expiry.'
            if running_dhcp_long in line:
                run_dhcp_long = True
        fd.close()
        return 'fail', 'No DHCP request received after lease expiry.'

    _write_report("{b}{t}\n{b}".format(b=dash_break_line, t=TEST_REQUEST))

    if TEST_REQUEST == 'connection.network.dhcp_short':
        result, summary = _test_dhcp_short()
        _write_report("{d}\n{b}".format(b=dash_break_line, d=description_dhcp_short))
    elif TEST_REQUEST == 'connection.network.dhcp_long':
        result, summary = _test_dhcp_long()
        _write_report("{d}\n{b}".format(b=dash_break_line, d=description_dhcp_long))
    

    _write_report("RESULT {r} {t} {s}\n".format(r=result, t=TEST_REQUEST, s=summary))


if __name__ == "__main__":
    main()
