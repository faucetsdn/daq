from __future__ import absolute_import, division
from scapy.all import NTP, rdpcap
import sys
import os

arguments = sys.argv

test_request = str(arguments[1])
startup_pcap_file = str(arguments[2])
monitor_pcap_file = str(arguments[3])

report_filename = 'ntp_tests.txt'
ignore = '%%'
summary_text = ''
result = 'fail'
dash_break_line = '--------------------\n'
description_ntp_support = 'Device supports NTP version 4.'
description_ntp_update = 'Device synchronizes its time to the NTP server.'

NTP_VERSION_PASS = 4
LOCAL_PREFIX = '10.20.'
NTP_SERVER_SUFFIX = '.2'
MODE_CLIENT = 3
MODE_SERVER = 4
YEAR_2500 = 16725225600
SECONDS_BETWEEN_1900_1970 = 2208988800
OFFSET_ALLOWANCE = 0.128
LEAP_ALARM = 3


def write_report(string_to_append):
    with open(report_filename, 'a+') as file_open:
        file_open.write(string_to_append)


# Extracts the NTP version from the first client NTP packet
def ntp_client_version(capture):
    client_packets = ntp_packets(capture, MODE_CLIENT)
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
    capture = rdpcap(startup_pcap_file)
    if len(capture) > 0:
        version = ntp_client_version(capture)
        if version is None:
            add_summary("No NTP packets received.")
            return 'skip'
        if version == NTP_VERSION_PASS:
            add_summary("Using NTPv" + str(NTP_VERSION_PASS) + ".")
            return 'pass'
        else:
            add_summary("Not using NTPv" + str(NTP_VERSION_PASS) + ".")
            return 'fail'
    else:
        add_summary("No NTP packets received.")
        return 'skip'


def test_ntp_update():
    startup_capture = rdpcap(startup_pcap_file)
    packets = ntp_packets(startup_capture)
    if os.path.isfile(monitor_pcap_file):
        monitor_capture = rdpcap(monitor_pcap_file)
        packets += ntp_packets(monitor_capture)
    if len(packets) < 2:
        add_summary("Not enough NTP packets received.")
        return 'skip'
    # Check that DAQ NTP server has been used
    using_local_server = False
    local_ntp_packets = []
    for packet in packets:
        # Packet is to or from local NTP server
        if ((packet.payload.dst.startswith(LOCAL_PREFIX) and
                packet.payload.dst.endswith(NTP_SERVER_SUFFIX)) or
                (packet.payload.src.startswith(LOCAL_PREFIX) and
                    packet.payload.src.endswith(NTP_SERVER_SUFFIX))):
            using_local_server = True
            local_ntp_packets.append(packet)
    if not using_local_server or len(local_ntp_packets) < 2:
        add_summary("Device clock not synchronized with local NTP server.")
        return 'fail'
    # Obtain the latest NTP poll
    p1 = p2 = p3 = p4 = None
    for i in range(len(local_ntp_packets)):
        if p1 is None:
            if ntp_payload(local_ntp_packets[i]).mode == MODE_CLIENT:
                p1 = local_ntp_packets[i]
        elif p2 is None:
            if ntp_payload(local_ntp_packets[i]).mode == MODE_SERVER:
                p2 = local_ntp_packets[i]
            else:
                p1 = local_ntp_packets[i]
        elif p3 is None:
            if ntp_payload(local_ntp_packets[i]).mode == MODE_CLIENT:
                p3 = local_ntp_packets[i]
        elif p4 is None:
            if ntp_payload(local_ntp_packets[i]).mode == MODE_SERVER:
                p4 = local_ntp_packets[i]
                p1 = p3
                p2 = p4
                p3 = p4 = None
            else:
                p3 = local_ntp_packets[i]
    if p1 is None or p2 is None:
        add_summary("Device clock not synchronized with local NTP server.")
        return 'fail'
    t1 = ntp_payload(p1).sent
    t2 = ntp_payload(p1).time
    t3 = ntp_payload(p2).sent
    t4 = ntp_payload(p2).time

    # Timestamps are inconsistenly either from 1900 or 1970
    if t1 > YEAR_2500:
        t1 = t1 - SECONDS_BETWEEN_1900_1970
    if t2 > YEAR_2500:
        t2 = t2 - SECONDS_BETWEEN_1900_1970
    if t3 > YEAR_2500:
        t3 = t3 - SECONDS_BETWEEN_1900_1970
    if t4 > YEAR_2500:
        t4 = t4 - SECONDS_BETWEEN_1900_1970

    offset = abs((t2 - t1) + (t3 - t4))/2
    if offset < OFFSET_ALLOWANCE and not ntp_payload(p1).leap == LEAP_ALARM:
        add_summary("Device clock synchronized.")
        return 'pass'
    else:
        add_summary("Device clock not synchronized with local NTP server.")
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
