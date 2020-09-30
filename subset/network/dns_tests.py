"""
    This script can be called to run DNS related test.

"""
from __future__ import absolute_import
import subprocess
import sys

import re
import datetime

arguments = sys.argv

test_request = str(arguments[1])
cap_pcap_file = str(arguments[2])
device_address = str(arguments[3])

report_filename = 'dns_tests.txt'
min_packet_length_bytes = 20
max_packets_in_report = 10
port_list = []
ignore = '%%'
summary_text = ''
result = 'fail'
dash_break_line = '--------------------\n'

DESCRIPTION_HOSTNAME_CONNECT = 'Check device uses the DNS server from DHCP and resolves hostnames'

TCPDUMP_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

IP_REGEX = r'(([0-9]{1,3}\.){3}[0-9]{1,3})'
RDATA_REGEX = r''

DNS_SERVER_HOST = '.2'


def write_report(string_to_append):
    print(string_to_append.strip())
    with open(report_filename, 'a+') as file_open:
        file_open.write(string_to_append)


def exec_tcpdump(tcpdump_filter, capture_file=None):
    """
    Args
        tcpdump_filter: Filter to pass onto tcpdump file
        capture_file: Optional capture file to look

    Returns
        List of packets matching the filter
    """

    capture_file = cap_pcap_file if capture_file is None else capture_file
    command = 'tcpdump -tttt -n -r {} {}'.format(capture_file, tcpdump_filter)

    process = subprocess.Popen(command,
                               universal_newlines=True,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    text = str(process.stdout.read()).rstrip()

    if text:
        return text.split("\n")

    return []


def add_summary(text):
    global summary_text
    summary_text = summary_text + " " + text if summary_text else text


def get_dns_server_from_ip(ip_address):
    """
    Returns the IP address of the DNS server provided by DAQ

    Args
        ip_address: IP address of the device under test

    Returns
        IP address of DNS server
    """

    return re.sub(r'\.\d+$', DNS_SERVER_HOST, ip_address)


def check_communication_for_response(response_line):
    """
    Given a line from the TCPdump output for DNS responses
    Look through the packet capture to see if any communitication to the
    IP addresses from the DNS

    Args
        tcpdump_line: Line from tcpdump filtered to DNS resposnes

    Returns
        True/False if the device has communicated with an IP from the
        DNS response after it has recieved it
    """

    response_time = datetime.datetime.strptime(response_line[:26], TCPDUMP_DATE_FORMAT)

    # Use regex to extract all IP addresses in the response
    matches = re.findall(IP_REGEX, response_line)

    # The first two IP addresses are the source/destination
    ip_addresses = matches[2:]

    for address in ip_addresses:
        packets = exec_tcpdump('dst host {}'.format(address[0]))
        for packet in packets:
            packet_time = datetime.datetime.strptime(packet[:26], TCPDUMP_DATE_FORMAT)
            if packet_time > response_time:
                return True

    return False


def test_dns(target_ip):
    """ Runs the dns.network.hostname_resolution test

    Checks that:
        i) the device sends DNS requests
        ii) the device uses the DNS server from DHCP
        iii) the device uses an IP address recieved from the DNS server

    Args
        target_ip: IP address of the device
    """

    # Get server IP of the DHCP server
    dhcp_dns_ip = get_dns_server_from_ip(target_ip)

    # Check if the device has sent any DNS requests
    filter_to_dns = 'dst port 53 and src host {}'.format(target_ip)
    to_dns = exec_tcpdump(filter_to_dns)
    num_query_dns = len(to_dns)

    if num_query_dns == 0:
        add_summary('Device did not send any DNS requests')
        return 'skip'

    # Check if the device only sent DNS requests to the DHCP Server
    filter_to_dhcp_dns = 'dst port 53 and src host {} and dst host {}' \
        .format(target_ip, dhcp_dns_ip)

    to_dhcp_dns = exec_tcpdump(filter_to_dhcp_dns)
    num_query_dhcp_dns = len(to_dhcp_dns)

    if num_query_dns > num_query_dhcp_dns:
        add_summary('Device sent DNS requests to servers other than the DHCP provided server')
        return 'fail'

    # Retrieve responses from DNS
    filter_dns_response = 'src port 53 and src host {}'.format(dhcp_dns_ip)
    dns_responses = exec_tcpdump(filter_dns_response)

    num_dns_responses = len(dns_responses)

    if num_dns_responses == 0:
        add_summary('No results recieved from DNS server')
        return 'fail'

    # Check that the device has sent data packets to any of the IP addresses it has recieved
    # it has recieved from the DNS requests

    for response in dns_responses:
        if check_communication_for_response(response):
            add_summary('Device sends DNS requests and resolves host names')
            return 'pass'

    add_summary('Device did not send data to IP addresses retrieved from the DNS server')
    return 'fail'


write_report("{b}{t}\n{b}".format(b=dash_break_line, t=test_request))

if test_request == 'dns.network.hostname_resolution':
    write_report("{d}\n{b}".format(b=dash_break_line, d=DESCRIPTION_HOSTNAME_CONNECT))
    result = test_dns(device_address)

write_report("RESULT {r} {t} {s}\n".format(r=result, t=test_request, s=summary_text.strip()))
