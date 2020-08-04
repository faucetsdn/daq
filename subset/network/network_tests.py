"""
    This script can be called to run a specific network module test.
    Currently supports:
    - connection.min_send
    - connection.dhcp_long
    - protocol.app_min_send
    - communication.type.broadcast
    - network.ntp.support
    Usage: python network_tests.py <test_to_run> <monitor.pcap file> <target_ip>
    E.g. python network_tests.py connection.min_send $MONITOR $TARGET_IP
"""
import subprocess, time, sys, json

import re
import datetime

arguments = sys.argv

test_request = str(arguments[1])
cap_pcap_file = str(arguments[2])
device_address = str(arguments[3])

report_filename = 'network_tests.txt'
min_packet_length_bytes = 20
max_packets_in_report = 10
port_list = []
ignore = '%%'
summary_text = ''
result = 'fail'
dash_break_line = '--------------------\n'

description_min_send = 'Device sends data at a frequency of less than 5 minutes.'
description_communication_type = 'Device sends unicast or broadcast packets.'

tcpdump_display_all_packets = 'tcpdump -tttt -n src host ' + device_address + ' -r ' + cap_pcap_file
tcpdump_display_udp_bacnet_packets = 'tcpdump -n udp dst portrange 47808-47809 -r ' + cap_pcap_file
tcpdump_display_arp_packets = 'tcpdump arp -n src host ' + device_address + ' -r ' + cap_pcap_file

tcpdump_display_broadcast_packets = 'tcpdump broadcast and src host ' + device_address + ' -r ' + cap_pcap_file
tcpdump_display_multicast_packets = 'tcpdump -n \'ip[16] & 240 = 224\' -r ' + cap_pcap_file

system_conf_file = "/config/inst/system.conf"
tcpdump_date_format = "%Y-%m-%d %H:%M:%S.%f"
min_send_seconds = 300
min_send_duration = "5 minutes"

def write_report(string_to_append):
    print(string_to_append.strip())
    with open(report_filename, 'a+') as file_open:
        file_open.write(string_to_append)


def shell_command_with_result(command, wait_time, terminate_flag):
    process = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    text = process.stdout.read()
    retcode = process.wait()
    time.sleep(wait_time)
    if terminate_flag:
        process.terminate()
    return str(text)


def add_packet_count_to_report(packet_type, packet_count):
    write_report("{i} {t} packets received={p}\n".format(i=ignore, t=packet_type, p=packet_count))


def add_packet_info_to_report(packets_received):
    packet_list = packets_received.strip().split("\n")
    outnum = min(len(packet_list), max_packets_in_report)
    for x in range(0, outnum):
        write_report("{i} {p}\n".format(i=ignore, p=packet_list[x]))
    write_report("{i} packets_count={p}\n".format(i=ignore, p=len(packet_list)))


def decode_shell_result(shell_result):
    if len(shell_result) > min_packet_length_bytes:
        packet_request_list = shell_result.rstrip().split("\n")
        packets_received = len(packet_request_list)
        return packets_received
    return 0


def packets_received_count(shell_result):
    if shell_result is None:
        return 0
    else:
        return decode_shell_result(shell_result)


def get_scan_length(config_file):
    """ Gets length of the monitor.pcap scan

    Reads the system.conf file to and returns the length of the monitor_scan

    Args:
        config_file: Location of system.conf file within test container

    Returns:
        Length of monitor scan in seconds

        If not defined, or system.conf could not be found
        returns false
    """

    scan_length = False
    try:
        with open(config_file) as file:
            for line in file:
                match = re.search(r'^monitor_scan_sec=(\d+)', line)
                if match:
                    matched_length = int(match.group(1))
                    # If scan length = 0 or not found, then monitor scan does not exist
                    scan_length = matched_length if matched_length > 0 else False
        return scan_length
    except Exception as e:
        write_report("Error encountered reading system.conf {}".format(e))
        return False


def add_summary(text):
    global summary_text
    summary_text = summary_text + " " + text if summary_text else text


def test_connection_min_send():
    """ Runs the connection.min_send test

    Tests if the device sends data packets of any type (inc data, NTP, etc)
    within a period of 5 minutes by looking through the monitor.pcap file

    The length of test can be configured using the min_send_seconds variable
    at the start of the file
    """

    # Get scan length
    scan_length = get_scan_length(system_conf_file)
    min_send_delta = datetime.timedelta(seconds=min_send_seconds)
    min_send_pass = False

    # The test scans the monitor.pcap, so if it's not found skip
    if not scan_length:
        add_summary("DAQ monitor scan not running, test skipped")
        return 'skip'

    arp_shell_result = shell_command_with_result(tcpdump_display_arp_packets, 0, False)
    arp_packets_received = packets_received_count(arp_shell_result)
    if arp_packets_received > 0:
        add_summary("ARP packets received.")

    shell_result = shell_command_with_result(tcpdump_display_all_packets, 0, False)
    all_packets = shell_result.splitlines()

    # Loop through tcpdump result and measure the time between succesive packets
    for i, packet in enumerate(all_packets):
        # datetime is the first 26 characters of the line
        packet_time = datetime.datetime.strptime(packet[:26], tcpdump_date_format)

        if i == 0:
            previous_packet_time = packet_time
            continue

        delta = packet_time - previous_packet_time
        if delta < min_send_delta:
            min_send_pass = True
            break

        previous_packet_time = packet_time

    add_packet_info_to_report(shell_result)

    if not min_send_pass:
        if scan_length > min_send_seconds:
            add_summary('Data packets were not sent at a frequency less than ' +
                        min_send_duration)
            return 'fail'
        else:
            add_summary('Please set DAQ monitor scan to be greater than ' +
                        min_send_duration)
            return 'skip'

    add_summary('Data packets were sent at a frequency of less than ' +
                min_send_duration)
    return 'pass'


def test_communication_type_broadcast():
    """ Runs the communication.type.broadcast DAQ test.
    Counts the number of unicast, broadcast and multicast packets sent.
    """

    broadcast_result = shell_command_with_result(tcpdump_display_broadcast_packets, 0, False)
    broadcast_packets = packets_received_count(broadcast_result)
    if broadcast_packets > 0:
        add_summary("Broadcast packets received.")
        add_packet_count_to_report("Broadcast", broadcast_packets)

    multicast_result = shell_command_with_result(tcpdump_display_multicast_packets, 0, False)
    multicast_packets = packets_received_count(multicast_result)
    if multicast_packets > 0:
        add_summary("Multicast packets received.")
        add_packet_count_to_report("Multicast", multicast_packets)

    unicast_result = shell_command_with_result(tcpdump_display_all_packets, 0, False)
    unicast_packets = packets_received_count(unicast_result) - broadcast_packets - multicast_packets
    if unicast_packets > 0:
        add_summary("Unicast packets received.")
        add_packet_count_to_report("Unicast", unicast_packets)

    return 'info'


write_report("{b}{t}\n{b}".format(b=dash_break_line, t=test_request))

if test_request == 'connection.min_send':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_min_send))
    result = test_connection_min_send()
elif test_request == 'communication.type.broadcast':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_communication_type))
    result = test_communication_type_broadcast()

write_report("RESULT {r} {t} {s}\n".format(r=result, t=test_request, s=summary_text.strip()))
