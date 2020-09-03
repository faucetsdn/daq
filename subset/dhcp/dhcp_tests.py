from __future__ import absolute_import
import sys
import json
from scapy.all import rdpcap, DHCP

arguments = sys.argv
test_request = str(arguments[1])

scan_file = '/scans/test_ipaddr.pcap'
module_config_file = '/config/device/module_config.json'
dhcp_ranges = []
report_filename = 'report.txt'
ignore = '%%'
summary_text = ''
dash_break_line = '--------------------\n'
description_dhcp_short = 'Reconnect device and check for DHCP request.'
description_dhcp_long = 'Wait for lease expiry and check for DHCP request.'
description_private_address = 'Device supports all private address ranges.'
result = None

DHCP_REQUEST = 3
DHCP_ACKNOWLEDGE = 5


with open(module_config_file) as json_file:
    json_data = json.load(json_file)
    dhcp_ranges = json_data['modules']['ipaddr']['dhcp_ranges']


def write_report(string_to_append):
    with open(report_filename, 'a+') as file_open:
        file_open.write(string_to_append)


def add_summary(text):
    global summary_text
    summary_text = summary_text + " " + text if summary_text else text


def get_dhcp_type(capture, dhcp_type, after=None):
    for packet in capture:
        if DHCP not in packet:
            continue
        if packet[DHCP].options[0][1] == dhcp_type:
            if after is None:
                return packet
            if packet.time > after:
                return packet
    return None


def get_dhcp_option(packet, option):
    for opt in packet[DHCP].options:
        if opt[0] == option:
            return opt[1]
    return None


def test_dhcp_short():
    capture = rdpcap(scan_file)
    dhcp_req = get_dhcp_type(capture, DHCP_REQUEST)
    if dhcp_req is None:
        add_summary('No DHCP request received.')
        return 'fail'
    add_summary('DHCP request received.')
    return 'pass'


def test_dhcp_long():
    capture = rdpcap(scan_file)
    dhcp_ack = get_dhcp_type(capture, DHCP_ACKNOWLEDGE)
    if dhcp_ack is None:
        add_summary('No DHCP request received after lease expiry.')
        return 'fail'
    lease_time = get_dhcp_option(dhcp_ack, 'lease_time')
    expiry = dhcp_ack.time + lease_time

    dhcp_req = get_dhcp_type(capture, DHCP_REQUEST, expiry)
    if dhcp_req is None:
        add_summary('No DHCP request received after lease expiry.')
        return 'fail'
    add_summary('DHCP request received after lease expiry.')
    return 'pass'


def to_ipv4(ip):
    return tuple(int(n) for n in ip.split('.'))


def in_range(ip, start, end):
    return to_ipv4(start) < to_ipv4(ip) < to_ipv4(end)


def supports_range(capture, start, end):
    found_request = False
    for packet in capture:
        if DHCP not in packet:
            continue
        if not packet[DHCP].options[0][1] == dhcp_request:
            continue
        if get_dhcp_option(packet, 'requested_addr') is None:
            continue
        if in_range(get_dhcp_option(packet, 'requested_addr'), start, end):
            found_request = True
    return found_request


def test_private_address():
    capture = rdpcap(scan_file)
    passing = True
    for dhcp_range in dhcp_ranges:
        if not supports_range(capture, dhcp_range['start'], dhcp_range['end']):
            passing = False
    if passing:
        add_summary('All private address ranges are supported.')
        return 'pass'
    add_summary('Not all private address ranges are supported.')
    return 'fail'


write_report("{b}{t}\n{b}".format(b=dash_break_line, t=test_request))


if test_request == 'connection.network.dhcp_short':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_dhcp_short))
    result = test_dhcp_short()
elif test_request == 'connection.network.dhcp_long':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_dhcp_long))
    result = test_dhcp_long()
elif test_request == 'connection.dhcp.private_address':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_private_address))
    result = test_private_address()

write_report("RESULT {r} {t} {s}\n".format(r=result, t=test_request, s=summary_text.strip()))
