from __future__ import absolute_import, division
import sys
import re
import json
import test_result
from scapy.all import NTP, rdpcap, DNS

arguments = sys.argv

test_request = str(arguments[1])
pcap_file = str(arguments[2])
device_address = str(arguments[3])

report_filename = 'ntp_tests.txt'

description_ntp_support = 'Device supports NTP version 4.'
description_ntp_update_dhcp = 'Device synchronizes its time to the NTP server using DHCP'
description_ntp_update_dns = 'Device synchronizes its time to the NTP server using DNS'

NTP_VERSION_PASS = 4
LOCAL_PREFIX = '10.20.'
NTP_SERVER_SUFFIX = '.2'
MODE_CLIENT = 3
MODE_SERVER = 4
YEAR_2500 = 16725225600
SECONDS_BETWEEN_1900_1970 = 2208988800
OFFSET_ALLOWANCE = 0.128
LEAP_ALARM = 3

IP_REGEX = r'(([0-9]{1,3}\.){3}[0-9]{1,3})'
NTP_SERVER_IP_SUFFIX = '.2'
NTP_SERVER_HOSTNAME = 'ntp.daqlocal'
MODULE_CONFIG_PATH = '/config/device/module_config.json'

TEST_DHCP = 'dhpc'
TEST_DNS = 'dns'

def write_report(string_to_append):
    with open(report_filename, 'a+') as file_open:
        file_open.write(string_to_append)


def ntp_client_version(capture):
    """ Extracts the NTP version from the first client NTP packet """
    client_packets = ntp_packets(capture, MODE_CLIENT)
    if len(client_packets) == 0:
        return None
    return ntp_payload(client_packets[0]).version


def ntp_packets(capture, mode=None):
    """ Filters the packets by type (NTP) """
    packets = []
    for packet in capture:
        if NTP in packet:
            ip = packet.payload
            udp = ip.payload
            ntp = udp.payload
            if mode is None or mode == ntp.mode:
                packets.append(packet)
    return packets


def ntp_configured_by_dns():
    """Checks module_config for parameter that NTP is configured using DNS

    Parameter must be (bool) True, else will be considered false
    """
    module_config =  open(MODULE_CONFIG_PATH)
    module_config = json.load(module_config)
    try:
        ntp_by_dns = (module_config['modules']['network']['ntp_dns'])
    except KeyError:
        ntp_by_dns = False

    return ntp_by_dns is True


def ntp_payload(packet):
    """ Extracts the NTP payload from a packet of type NTP """
    ip = packet.payload
    udp = ip.payload
    ntp = udp.payload
    return ntp


def dns_requests_for_hostname(hostname, packet_capture):
    """Checks for DNS requests for a given hostname

    Args:
        packet_capture  path to tcpdump packet capture file
        hostname        hostname to look for

    Returns:
        true/false if any matching DNS requests detected to hostname
    """
    capture = rdpcap(packet_capture)
    fqdn = hostname + '.'
    for packet in capture:
        if DNS in packet:
            if packet.qd.qname.decode("utf8") == fqdn:
                return True
    return False


def ntp_server_from_ip(ip_address):
    """Returns the IP address of the NTP server provided by DAQ

    Args:
        ip_address: IP address of the device under test

    Returns:
        IP address of NTP server
    """
    return re.sub(r'\.\d+$', NTP_SERVER_IP_SUFFIX, ip_address)


def check_ntp_synchronized(ntp_packets_array, ntp_server_ip):
    """ Checks if NTP packets indicate a device is syncronized with the provided
    IP address

    Args:
        packet_capture  Array of scapy object of packet capture with NTP
                        packets from  ntp_packets()
        ntp_server_ip   IP address of server to checK

    Returns:
        boolean true/false if synchronized with provided NTP server.
    """

    local_ntp_packets = []
    using_given_server = False
    for packet in ntp_packets_array:
        # Packet is to or from NTP server
        if (packet.payload.dst == ntp_server_ip or packet.payload.src == ntp_server_ip):
            using_given_server = True
            local_ntp_packets.append(packet)

    if not using_given_server or len(local_ntp_packets) < 2:
        return False

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
        return False

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
        return True
    else:
        return False


def test_ntp_support():
    """ Tests support for NTPv4 """
    capture = rdpcap(pcap_file)
    packets = ntp_packets(capture)
    test_ntp = test_result.test_result( name='ntp.network.ntp_support',
                                        description=description_ntp_support)
    if len(packets) > 0:
        version = ntp_client_version(packets)
        if version is None:
            test_ntp.add_summary("No NTP packets received.")
            test_ntp.result = test_result.SKIP
        if version == NTP_VERSION_PASS:
            test_ntp.add_summary("Using NTPv" + str(NTP_VERSION_PASS) + ".")
            test_ntp.result = test_result.PASS
        else:
            test_ntp.add_summary("Not using NTPv" + str(NTP_VERSION_PASS) + ".")
            test_ntp.result = test_result.FAIL
    else:
        test_ntp.add_summary("No NTP packets received.")
        test_ntp.result = test_result.SKIP

    test_ntp.write_results(report_filename)


def test_ntp_update():
    """Runs NTP Update Test for both DHCP and DNS"""
    # Used to always print test output in the same order 
    ntp_tests = {}
    ntp_tests[TEST_DHCP] = test_result.test_result(
        name='ntp.network.ntp_update_dhcp',
        description=description_ntp_update_dhcp)
    ntp_tests[TEST_DNS] = test_result.test_result(
        name='ntp.network.ntp_update_dns',
        description=description_ntp_update_dns)
    
    capture = rdpcap(pcap_file)
    packets = ntp_packets(capture)

    if len(packets) < 2:
        for test in ntp_tests:
            ntp_tests[test].add_summary("Not enough NTP packets received.")
            ntp_tests[test].result = test_result.SKIP
            ntp_tests[test].write_results(report_filename)
    else:
        test_dns = ntp_configured_by_dns()
        local_ntp_ip = ntp_server_from_ip(device_address)
        device_sync_local_server = check_ntp_synchronized(packets, local_ntp_ip)

        if test_dns:
            active_test = TEST_DNS
            ntp_tests[TEST_DHCP].add_summary("Device not configured for NTP via DHCP")
            ntp_tests[TEST_DHCP].result = test_result.SKIP
        else:
            active_test = TEST_DHCP
            ntp_tests[TEST_DNS].add_summary("Device not configured for NTP via DNS")
            ntp_tests[TEST_DNS].result = test_result.SKIP

        if device_sync_local_server:
            ntp_tests[active_test].add_summary("Device clock synchronized.")
            ntp_tests[active_test].result = test_result.PASS
        else:
            ntp_tests[active_test].add_summary("Device clock not synchronized with local NTP server.")
            ntp_tests[active_test].result = test_result.FAIL

    ntp_tests[TEST_DHCP].write_results(report_filename)
    ntp_tests[TEST_DNS].write_results(report_filename)

if test_request == 'ntp.network.ntp_support':
    test_ntp_support()
elif test_request == 'ntp.network.ntp_update':
    test_ntp_update()
