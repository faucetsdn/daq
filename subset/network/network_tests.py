import subprocess, time, sys, json

arguments = sys.argv

test_request = str(arguments[1])
cap_pcap_file = str(arguments[2])
device_address = str(arguments[3])

if test_request == 'protocol.app_min_send':
    module_config = str(arguments[4])
    infastructure_excludes = str(arguments[5])

report_filename = 'report.txt'
min_packet_length_bytes = 20
max_packets_in_report = 10
packet_request_list = []
port_list = []
ignore = '%%'
summary = ''
result = 'fail'
dash_break_line = '--------------------\n'
description_min_send = 'Device sends data at a frequency of less than 5 minutes.'
description_dhcp_long = 'Device sends ARP request on DHCP lease expiry.'
description_app_min_send = 'Device sends application packets at a frequency of less than 5 minutes.'
description_communication_type = 'Device sends unicast or broadcast packets.'
description_ntp_support = 'Device sends NTP request packets.'

tcpdump_display_all_packets = 'tcpdump -n src host ' + device_address + ' -r ' + cap_pcap_file
tcpdump_display_udp_bacnet_packets = 'tcpdump -n udp dst portrange 47808-47809 -r ' + cap_pcap_file
tcpdump_display_arp_packets = 'tcpdump arp -r ' + cap_pcap_file
tcpdump_display_ntp_packets = 'tcpdump dst port 123 -r ' + cap_pcap_file
tcpdump_display_eapol_packets = 'tcpdump port 1812 or port 1813 or port 3799 -r ' + cap_pcap_file
tcpdump_display_broadcast_packets = 'tcpdump broadcast -r ' + cap_pcap_file

def write_report(string_to_append):
    with open(report_filename, 'a+') as file_open:
        file_open.write(string_to_append)

def shell_command_with_result(command, wait_time, terminate_flag):
    process = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    text = process.stdout.read()
    retcode = process.wait()
    time.sleep(wait_time)
    if terminate_flag:
        process.terminate()
    if len(text) > 0:
        return text

def add_packet_info_to_report(packets_received, packet_request_list):
    global max_packets_in_report
    if packets_received > max_packets_in_report:
        max = max_packets_in_report
    else:
        max = packets_received
    for x in range(0, max):
        write_report("{i} {p}\n".format(i=ignore, p=packet_request_list[x]))
    write_report("{i} packets_count={p}\n".format(i=ignore, p=packets_received))

def decode_shell_result(shell_result):
    global packet_request_list
    if len(shell_result) > min_packet_length_bytes:
        packet_request_list = shell_result.split("\n")
        packets_received = len(packet_request_list)
        return packets_received

def packets_received_count(shell_result):
    if shell_result is None:
        return 0
    else:
        return decode_shell_result(shell_result)

def load_json_config(json_filename):
    with open(json_filename, 'r') as json_file:
        return json.load(json_file)

def add_to_port_list(port_map):
    global port_list
    for port, port_info in port_map.items():
        for key, value in port_info.items():
            if key == 'allowed':
                if value == True:
                    port_list.append(port)

def remove_from_port_list(port_map):
    global port_list
    for exclude in port_map:
        for port in port_list:
            if port == exclude:
                port_list.remove(exclude)

def decode_json_config(config_file, map_name, action):
    dictionary = load_json_config(config_file)
    for key, value in dictionary.items():
        if key == map_name:
            for protocol, info in value.items():
                if protocol == 'udp' or protocol == 'tcp':
                    for ports, port_map in info.items():
                        if action == 'add':
                            add_to_port_list(port_map)
                        elif action == 'remove':
                            remove_from_port_list(port_map)

def test_connection_min_send():
    shell_result = shell_command_with_result(tcpdump_display_arp_packets, 0, False)
    arp_packets_received = packets_received_count(shell_result)
    if arp_packets_received > 0:
        add_summary("ARP packets received. ")
    shell_result = shell_command_with_result(tcpdump_display_all_packets, 0, False)
    all_packets_received = packets_received_count(shell_result)
    if (all_packets_received - arp_packets_received) > 0:
        add_summary("Packets received.\n")
        add_packet_info_to_report(arp_packets_received, packet_request_list)
        return 'pass'
    else:
        return 'fail'

def test_connection_dhcp_long():
    shell_result = shell_command_with_result(tcpdump_display_arp_packets, 0, False)
    arp_packets_received = packets_received_count(shell_result)
    if arp_packets_received > 0:
        add_summary("ARP packets received.\n")
        add_packet_info_to_report(arp_packets_received, packet_request_list)
        return 'pass'
    else:
        return 'fail'

def test_protocol_app_min_send():
    """
    reads module_config json file and adds ports to port_list
    read infastructure_excludes json file and removes ports from port_list (temporarily commented)
    """
    decode_json_config(module_config, 'servers', 'add')
    #decode_json_config(infastructure_excludes, 'excludes', 'remove')
    print('port_list:')
    app_packets_received = 0
    for port in port_list:
        print(port)
        tcpdump_filter = 'tcpdump port {p} -r {c}'.format(p=port, c=cap_pcap_file)
        shell_result = shell_command_with_result(tcpdump_filter, 0, False)
        app_packets_received += packets_received_count(shell_result)
    if app_packets_received > 0:
        add_summary("Application packets received.\n")
        add_packet_info_to_report(app_packets_received, packet_request_list)
        return 'pass'
    else:
        return 'fail'

def test_communication_type_broadcast():
    shell_result = shell_command_with_result(tcpdump_display_broadcast_packets, 0, False)
    broadcast_packets_received = packets_received_count(shell_result)
    if broadcast_packets_received > 0:
        add_summary("Broadcast packets received. ")
    shell_result = shell_command_with_result(tcpdump_display_all_packets, 0, False)
    all_packets_received = packets_received_count(shell_result)
    if (all_packets_received - broadcast_packets_received) > 0:
        add_summary("Unicast packets received.\n")
    return 'info'

def test_ntp_support():
    shell_result = shell_command_with_result(tcpdump_display_ntp_packets, 0, False)
    ntp_packets_received = packets_received_count(shell_result)
    if ntp_packets_received > 0:
        add_summary("NTP packets received.\n")
        add_packet_info_to_report(ntp_packets_received, packet_request_list)
        return 'pass'
    else:
        return 'fail'

def add_summary(text):
    global summary
    summary += text

write_report("{b}{t}\n{b}".format(b=dash_break_line, t=test_request))

if test_request == 'connection.min_send':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_min_send))
    result = test_connection_min_send()
elif test_request == 'connection.dhcp_long':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_dhcp_long))
    result = test_connection_dhcp_long()
elif test_request == 'protocol.app_min_send':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_app_min_send))
    result = test_protocol_app_min_send()
elif test_request == 'communication.type.broadcast':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_communication_type))
    result = test_communication_type_broadcast()
elif test_request == 'network.ntp.support':
    write_report("{d}\n{b}".format(b=dash_break_line, d=description_ntp_support))
    result = test_ntp_support()

write_report("RESULT {r} {t} {s}\n".format(r=result, t=test_request, s=summary))
