from __future__ import absolute_import
import time
import sys
import os
from scapy.all import rdpcap, DHCP, BOOTP

arguments = sys.argv
test_request = str(arguments[1])

scan_file = '/scans/test_ipaddr.pcap'
report_filename = 'report.txt'
ignore = '%%'
summary_text = ''
dash_break_line = '--------------------\n'
description_dhcp_short = 'Reconnect device and check for DHCP request.'
description_dhcp_long = 'Wait for lease expiry and check for DHCP request.'
result = None

dhcp_request = 3
dhcp_acknowledge = 5


def write_report(string_to_append):
    with open(report_filename, 'a+') as file_open:
        file_open.write(string_to_append)


def add_summary(text):
        global summary_text
        summary_text = summary_text + " " + text if summary_text else text


def get_dhcp_type(capture, dhcp_type, after=None):
    for packet in capture:
        if not DHCP in packet:
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
    dhcp_req = get_dhcp_type(capture, dhcp_request)
    if dhcp_req is None:
        add_summary('No DHCP request received.')
        return 'fail'
    add_summary('DHCP request received.')
    return 'pass'

def test_dhcp_long():
    capture = rdpcap(scan_file)
    dhcp_ack = get_dhcp_type(capture, dhcp_acknowledge)
    if dhcp_ack is None:
        add_summary('No DHCP request received after lease expiry.')
        return 'fail'
    lease_time = get_dhcp_option(dhcp_ack, 'lease_time')
    expiry = dhcp_ack.time + lease_time

    dhcp_req = get_dhcp_type(capture, dhcp_request, expiry)
    if dhcp_req is None:
        add_summary('No DHCP request received after lease expiry.')
        return 'fail'
    add_summary('DHCP request received after lease expiry.')
    return 'pass'


write_report("{b}{t}\n{b}".format(b=dash_break_line, t=test_request))


if test_request == 'connection.network.dhcp_short':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_dhcp_short))
    result = test_dhcp_short()
    
elif test_request == 'connection.network.dhcp_long':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_dhcp_long))
    result = test_dhcp_long()

write_report("RESULT {r} {t} {s}\n".format(r=result, t=test_request, s=summary_text.strip()))
