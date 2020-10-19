from __future__ import absolute_import
import sys
import json
from scapy.all import rdpcap, DHCP, ICMP, IP

TEST_REQUEST = str(sys.argv[1])
DHCP_REQUEST = 3
DHCP_ACKNOWLEDGE = 5

def main():
    """main"""
    scan_file = '/scans/test_ipaddr.pcap'
    ipaddr_log = '/tmp/activate.log'
    module_config_file = '/config/device/module_config.json'
    dhcp_ranges = []
    scan_file = '/scans/test_ipaddr.pcap'
    report_filename = 'report.txt'
    dash_break_line = '--------------------\n'
    description_dhcp_short = 'Reconnect device and check for DHCP request.'
    description_ip_change = 'Device communicates after IP change.'
    description_private_address = 'Device supports all private address ranges.'
    description_dhcp_change = 'Device receives new IP address after IP change and port toggle.'
    running_port_toggle = 'Running dhcp port_toggle test'
    running_dhcp_change = 'Running dhcp change test'
    running_ip_change = 'Running ip change test'
    ip_notification = 'ip notification'
    result = None
    summary = None

    with open(module_config_file) as json_file:
        json_data = json.load(json_file)
        dhcp_ranges = json_data['modules']['ipaddr']['dhcp_ranges']

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

    def _to_ipv4(ip):
        return tuple(int(n) for n in ip.split('.'))

    def _in_range(ip, start, end):
        return _to_ipv4(start) < _to_ipv4(ip) < _to_ipv4(end)

    def _supports_range(capture, start, end):
        found_request = False
        for packet in capture:
            if DHCP not in packet:
                continue
            if not packet[DHCP].options[0][1] == DHCP_REQUEST:
                continue
            if _get_dhcp_option(packet, 'requested_addr') is None:
                continue
            if _in_range(_get_dhcp_option(packet, 'requested_addr'), start, end):
                found_request = True
        return found_request

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

    def _test_private_address():
        if len(dhcp_ranges) == 0:
            return 'skip', 'No private address ranges were specified.'
        capture = rdpcap(scan_file)
        passing = True
        for dhcp_range in dhcp_ranges:
            if not _supports_range(capture, dhcp_range['start'], dhcp_range['end']):
                passing = False
        if passing:
            return 'pass', 'All private address ranges are supported.'
        return 'fail', 'Not all private address ranges are supported.'

    def _test_dhcp_change():
        fd = open(ipaddr_log, 'r')
        run_dhcp_change = False
        dhcp_change_ip = None
        for line in fd:
            if run_dhcp_change:
                if ip_notification in line:
                    dhcp_change_ip = line.split(ip_notification + ' ')[1].rstrip()
                    break
            if running_dhcp_change in line:
                run_dhcp_change = True
        fd.close()

        capture = rdpcap(scan_file)
        pingFound = False
        for packet in capture:
            if ICMP in packet and packet[IP].src == dhcp_change_ip:
                pingFound = True
        if pingFound:
            return 'pass', 'Device has received new IP address.'
        return 'fail', 'Device has not received new IP address.'

    _write_report("{b}{t}\n{b}".format(b=dash_break_line, t=TEST_REQUEST))

    if TEST_REQUEST == 'connection.ipaddr.dhcp_disconnect':
        result, summary = _test_dhcp_short()
        _write_report("{d}\n{b}".format(b=dash_break_line, d=description_dhcp_short))
    elif TEST_REQUEST == 'connection.ipaddr.ip_change':
        result, summary = _test_ip_change()
        _write_report("{d}\n{b}".format(b=dash_break_line, d=description_ip_change))
    elif TEST_REQUEST == 'connection.ipaddr.private_address':
        result, summary = _test_private_address()
        _write_report("{d}\n{b}".format(b=dash_break_line, d=description_private_address))
    elif TEST_REQUEST == 'connection.ipaddr.disconnect_ip_change':
        result, summary = _test_dhcp_change()
        _write_report("{d}\n{b}".format(b=dash_break_line, d=description_dhcp_change))

    _write_report("RESULT {r} {t} {s}\n".format(r=result, t=TEST_REQUEST, s=summary))


if __name__ == "__main__":
    main()
