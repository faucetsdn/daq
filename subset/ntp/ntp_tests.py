from __future__ import absolute_import, division
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
description_ntp_update = 'Device synchronizes its time to the NTP server.'


def write_report(string_to_append):
    with open(report_filename, 'a+') as file_open:
        file_open.write(string_to_append)


# Extracts the NTP version from the first client NTP packet
def ntp_client_version(capture):
    client_packets = ntp_packets(capture, 3)
    if len(client_packets) == 0:
        return None
    return ntp_payload(client_packets[0]).version


# Filters the packets by type (NTP)
def ntp_packets(capture, mode=None):
    packets = []
    for packet in capture:
        if NTP in packet:
            ip = packet.payload
            udp = ip.payload
            ntp = udp.payload
            if mode is None or mode == ntp.mode:
                packets.append(packet)
    return packets


# Extracts the NTP payload from a packet of type NTP
def ntp_payload(packet):
    ip = packet.payload
    udp = ip.payload
    ntp = udp.payload
    return ntp


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


def test_ntp_update():
    capture = rdpcap(cap_pcap_file)
    packets = ntp_packets(capture)
    if len(packets) < 4:
        add_summary("Not enough NTP packets received.")
        return 'skip'
    # Check that DAQ NTP server has been used
    local_device = local_ntp_server = None
    using_local_server = False
    local_ntp_packets = []
    for packet in packets:
        # Packet is to or from local NTP server
        if ((packet.payload.dst.startswith('10.20.') and packet.payload.dst.endswith('.2')) or
                (packet.payload.src.startswith('10.20.') and packet.payload.src.endswith('.2'))):
            using_local_server = True
            local_ntp_packets.append(packet)
    if not using_local_server:
        add_summary("Device clock not synchronized with local NTP server.")
        return 'fail'
    if len(local_ntp_packets) < 4:
        add_summary("Device clock not synchronized with local NTP server.")
        return 'fail'
    # Ensuring the correct sequence of ntp packets are collated
    p1 = p2 = p3 = p4 = None
    for i in range(len(local_ntp_packets)):
        if p1 is None:
            if ntp_payload(local_ntp_packets[i]).mode == 3:
                p1 = local_ntp_packets[i]
                continue
        if p2 is None:
            if ntp_payload(local_ntp_packets[i]).mode == 4:
                p2 = local_ntp_packets[i]
            else:
                p1 = None
            continue
        if p3 is None:
            if ntp_payload(local_ntp_packets[i]).mode == 3:
                p3 = local_ntp_packets[i]
                continue
        if p4 is None:
            if ntp_payload(local_ntp_packets[i]).mode == 4:
                p4 = local_ntp_packets[i]
            else:
                p3 = None
            continue
    if p1 is None or p2 is None or p3 is None or p4 is None:
        add_summary("Device clock not synchronized with local NTP server. One of 4 packets is None")
        return 'fail'
    offset = ((ntp_payload(p2).recv - ntp_payload(p1).sent) +
            (ntp_payload(p3).sent - ntp_payload(p4).recv))/2
    if offset < 1:
        add_summary("Device clock synchronized.")
        return 'pass'
    else:
        add_summary("Device clock not synchronized with local NTP server. Offset is " + str(offset))
        return 'fail'


def add_summary(text):
    global summary_text
    summary_text = summary_text + " " + text if summary_text else text


write_report("{b}{t}\n{b}".format(b=dash_break_line, t=test_request))


if test_request == 'connection.network.ntp_support':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_ntp_support))
    result = test_ntp_support()
elif test_request == 'connection.network.ntp_update':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_ntp_update))
    result = test_ntp_update()

write_report("RESULT {r} {t} {s}\n".format(r=result, t=test_request, s=summary_text.strip()))
