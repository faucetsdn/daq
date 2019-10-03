import socket, sys, time

arguments = sys.argv

udp_ip_address = str(arguments[1])
udp_port = int(arguments[2])
transport_type = str(arguments[3])
duration_seconds = int(arguments[4])
cycle_seconds = int(arguments[5])
multicast_ttl = 2
message = "Fried lizards taste like chicken"

def multicast_setup_socket():
    #https://www.tldp.org/HOWTO/Multicast-HOWTO-6.html)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    client.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, multicast_ttl)
    return client

def broadcast_setup_socket():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return client

def send_message(message, transport_type):
    if transport_type == 'broadcast':
        client = broadcast_setup_socket()
    elif transport_type == 'multicast':
        client = multicast_setup_socket()
    sent = client.sendto(message, (udp_ip_address, udp_port))

while(duration_seconds > 0):
    print('{t} to {a}'.format(t=transport_type, a=udp_ip_address))
    send_message(message, transport_type)
    time.sleep(cycle_seconds)
    duration_seconds -= cycle_seconds
