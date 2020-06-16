import subprocess, time, sys, json

import datetime

arguments = sys.argv

#test_request = str(arguments[1])
#cap_pcap_file = str(arguments[2])
#device_address = str(arguments[3])
cap_pcap_file = "mqtt.pcap"
device_address = "192.168.86.88"

report_filename = 'report.txt'
min_packet_length_bytes = 20
max_packets_in_report = 10
port_list = []
ignore = '%%'
summary_text = ''
result = 'fail'
dash_break_line = '--------------------\n'
description_min_send = 'Device sends data at a frequency of less than 5 minutes.'
description_dhcp_long = 'Device sends ARP request on DHCP lease expiry.'
description_app_min_send = 'Device sends application packets at a frequency of less than 5 minutes.'
description_communication_type = 'Device sends unicast or broadcast packets.'
description_ntp_support = 'Device sends NTP request packets.'

tcpdump_display_all_packets = 'tcpdump -tttt -n src host ' + device_address + ' -r ' + cap_pcap_file
tcpdump_display_udp_bacnet_packets = 'tcpdump -n udp dst portrange 47808-47809 -r ' + cap_pcap_file
tcpdump_display_arp_packets = 'tcpdump arp -n src host ' + device_address + ' -r ' + cap_pcap_file
tcpdump_display_ntp_packets = 'tcpdump dst port 123 -r ' + cap_pcap_file
tcpdump_display_eapol_packets = 'tcpdump port 1812 or port 1813 or port 3799 -r ' + cap_pcap_file
tcpdump_display_broadcast_packets = 'tcpdump broadcast and src host ' + device_address + ' -r ' + cap_pcap_file

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
    write_report("{i} {t} Packets recieved={p}\n".format(i=ignore, t=packet_type, p=packet_count))

def add_packet_info_to_report(packets_received):
    packet_list = packets_received.rstrip().split("\n")
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


def add_to_port_list(port_map):
    global port_list
    for port, port_info in port_map.items():
        for key, value in port_info.items():
            if key == 'allowed':
                if value == True:
                    port_list.append(port)

def test_connection_min_send():
    arp_shell_result = shell_command_with_result(tcpdump_display_arp_packets, 0, False)
    arp_packets_received = packets_received_count(arp_shell_result)
    print(arp_packets_received)
    if arp_packets_received > 0:
        add_summary("ARP packets received.")
    shell_result = shell_command_with_result(tcpdump_display_all_packets, 0, False)
    
    all_packets = shell_result.splitlines()
    i=0

    min_send_duration = datetime.timedelta(minutes=5)
    min_send_pass = False
    
    # date format of tcpdump using -tttt
    date_format = "%Y-%m-%d %H:%M:%S.%f" 

    # Loop through tcpdump result
    # measure the time between packets

    for packet in all_packets:
        i = i + 1 
        
        # datetime is the first 26 characters 
        packet_time = datetime.datetime.strptime(packet[:26], date_format) 
        
        if i == 1:
            previous_packet_time = packet_time
            continue
        
        delta = packet_time - previous_packet_time

        # test passes if frequency exceeds the min send duration
        if delta < min_send_duration:
            min_send_pass = True
            break

        # set at end of loop so we can compare against it next iteration
        previous_packet_time = packet_time 
    
    # check test duration
    # skip if test is less than 5 minutes
    # as the test results are inconclusive
    if not min_send_pass:
        

    all_packets_received = packets_received_count(shell_result)
    print(all_packets_received)
    app_packets_received = all_packets_received - arp_packets_received
    if app_packets_received > 0:
        add_summary("Other packets received.")
    print('min_send_packets', arp_packets_received, all_packets_received)
    add_packet_info_to_report(shell_result)
    return 'pass' if app_packets_received > 0 else 'fail'


def add_summary(text):
    global summary_text
    summary_text = summary_text + " " + text if summary_text else text
test_request = 'connection.min_send'
write_report("{b}{t}\n{b}".format(b=dash_break_line, t=test_request))

result = test_connection_min_send()
write_report("RESULT {r} {t} {s}\n".format(r=result, t=test_request, s=summary_text.strip()))
