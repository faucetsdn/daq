from __future__ import absolute_import
import sys
from scapy.all import NTP, rdpcap

arguments = sys.argv

test_request = str(arguments[1])
cap_pcap_file = str(arguments[2])

report_filename = 'report.txt'
ignore = '%%'
summary_text = ''
result = 'fail'
dash_break_line = '--------------------\n'
description_ntp_support = 'Device supports NTP version 4.'


def write_report(string_to_append):
    with open(report_filename, 'a+') as file_open:
        file_open.write(string_to_append)


# Extracts the NTP version from the first client NTP packet
def ntp_client_version(capture):
    client_packets = ntp_packets(capture, 3)
    if len(client_packets) == 0:
        return None
    return client_packets[0].version


# Filters the packets by type (NTP)
def ntp_packets(capture, mode=None):
    packets = []
    for packet in capture:
        if NTP in packet:
            ip = packet.payload
            udp = ip.payload
            ntp = udp.payload
            if mode is None or mode == ntp.mode:
                packets.append(ntp)
    return packets


def test_ntp_support():
    capture = rdpcap(cap_pcap_file)
    if len(capture) > 0:
        version = ntp_client_version(capture)
        if version is None:
            add_summary("No NTP packets received.")
            return 'skip'
        if version == 4:
            add_summary("Using NTPv4.")
            return 'pass'
        else:
            add_summary("Not using NTPv4.")
            return 'fail'
    else:
        add_summary("No NTP packets received.")
        return 'skip'


def add_summary(text):
    global summary_text
    summary_text = summary_text + " " + text if summary_text else text


write_report("{b}{t}\n{b}".format(b=dash_break_line, t=test_request))


if test_request == 'connection.network.ntp_support':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_ntp_support))
    result = test_ntp_support()

write_report("RESULT {r} {t} {s}\n".format(r=result, t=test_request, s=summary_text.strip()))
