#!/bin/bash
set +x

REMOTE_IP="192.168.21.1"
LOCAL_IP="192.168.21.2"

# create dummy i/f and assign IP
sudo ip link add dummy0 type dummy
sudo ip addr add 192.168.21.2/24 dev dummy0
sudo ip link set dummy0 up

# socat session to move packets from ssh tunnel to UDP port
socat -T15 tcp4-listen:30001,reuseaddr,fork UDP:localhost:4789 &

# iptables command to change source IP from localhost
sudo iptables -t nat -A POSTROUTING -p udp -d 127.0.0.1 --dport 4789 -j SNAT --to-source 192.168.21.1:38000-45000

# iptables rule to divert traffic from dummy:4789 to UDP port
sudo iptables -t nat -A OUTPUT -o dummy0 -p udp --dport 4789 -j REDIRECT --to-ports 20000

# socat session to move packets from UDP port to ssh session
socat -T15 udp4-recvfrom:20000,reuseaddr,fork tcp:localhost:30000 &

# create vxlan tunnel
sudo ip link add vxlan type vxlan id 0 remote 192.168.21.1 dstport 4789 srcport 4789 4789 nolearning
sudo ip addr add 192.168.1.2/24 dev vxlan
sudo ip link set vxlan up



