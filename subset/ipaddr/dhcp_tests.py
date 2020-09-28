from __future__ import absolute_import
import sys
from scapy.all import rdpcap, DHCP, ICMP, IP

TEST_REQUEST = str(sys.argv[1])
DHCP_REQUEST = 3
DHCP_ACKNOWLEDGE = 5

def main():
    """main"""
    ipaddr_log = '/tmp/activate.log'
    scan_file = '/scans/test_ipaddr.pcap'
    report_filename = 'report.txt'
    dash_break_line = '--------------------\n'
    description_dhcp_short = 'Reconnect device and check for DHCP request.'
    description_dhcp_long = 'Wait for lease expiry and check for DHCP request.'
    description_ip_change = 'Device communicates after IP change.'
    running_port_toggle = 'Running dhcp port_toggle test'
    running_ip_change = 'Running ip change test'
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

    def _test_ip_change():

        fd = open(ipaddr_log, 'r')
        run_ip_change = False
        ip_change_ip = None
        for line in fd:
            if run_ip_change:
                if ip_notification in line:
                    ip_change_ip = line.split(ip_notification + ' ')[1].rstrip()
                    break
            if running_ip_change in line:
                run_ip_change = True
        fd.close()

        if ip_change_ip is None:
            return 'skip', 'IP change test did not run.'

        capture = rdpcap(scan_file)
        pingFound = False
        for packet in capture:
            if ICMP in packet and packet[IP].src == ip_change_ip:
                pingFound = True
        if pingFound:
            return 'pass', 'Ping response received after IP change.'
        return 'fail', 'No ping response received after IP change.'

    _write_report("{b}{t}\n{b}".format(b=dash_break_line, t=TEST_REQUEST))

    if TEST_REQUEST == 'connection.network.dhcp_short':
        result, summary = _test_dhcp_short()
        _write_report("{d}\n{b}".format(b=dash_break_line, d=description_dhcp_short))
    elif TEST_REQUEST == 'connection.dhcp.ip_change':
        result, summary = _test_ip_change()
        _write_report("{d}\n{b}".format(b=dash_break_line, d=description_ip_change))

    _write_report("RESULT {r} {t} {s}\n".format(r=result, t=TEST_REQUEST, s=summary))


if __name__ == "__main__":
    main()
