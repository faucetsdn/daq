# Data flow walkthrough

Overview:

device &rarr; sec switch &rarr; switch-link &rarr; pri switch &rarr; gateway set &rarr; docker

* _device_: Source device, either physical or virtual.
* _sec switch_: Secondary switch, either physical or virtual.
* _switch-link_: Data-plane link between sec and pri switch. Either physical or virtual.
* _pri switch_: Virtual internal primary switch.
* _gateway set_: Set of containers representing one device group.
* _docker_: Container providing core functionality (e.g. gateway, DHCP server, or test host).

If devices are in a group, then they will share the same gateway set. So,
gateway set 1 does not always correspond to the device on port 1. Check
the logs.

## Device-port

USB interface or virtual: `tcpdump` on Linux interface, as specified by the `intf_names`
configuration parameter.

Using physical switch: Can't do much about it, since it's local to the physical switch.

## Switch link

Hooked into the _pri switch_ on `ext_intf`, else 'pri-eth1' (default). Use `tcpdump` to monitor
traffic. This interface multiplexes traffic from all devices, so requires some filtering to
be meaningful. Some of it is duplicated on a vlan (10), others are raw packets.  Can filter by
IP address & port.

# Gateway set.

Device port 1 is handled by ports 10-19 on the primary switch, with interfaces pri-eth10
to pri-eth19. You can tap in there to see where data is doing into/out-of modules, e.g.:

* `pri-eth10`: gateway for port set 1, including DHCP server
* `pri-eth11`: dummy test host
* `pri-eth12`: running test (e.g. ping, hold, bacnet, nmap, etc..)

# Docker containers

See `docker ps` for the containers. They should be fairly direct what they are. You can get into
the containers and then run tcpdump there to see what traffic is flowing. If you use the `-k`
runtime option, then the system will create and <b>k</b>eep (forever) a test container, e.g.:

* _Window 1_: `cmd/run -k`
* _Window 2_: `docker exec -ti daq-hold01 bash`

# Sample path

Setup with virtual switching using `intf_names=faux`:
<pre>
~/daq$ <b>ip link show faux</b>
2209: faux@if2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master ovs-system state UP mode DEFAULT group default qlen 1000
    link/ether 42:b0:c3:25:02:5f brd ff:ff:ff:ff:ff:ff link-netnsid 0
~/daq$ <b>ip link show pri-eth1</b>
2213: pri-eth1@sec-eth7: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master ovs-system state UP mode DEFAULT group default qlen 1000
    link/ether ce:5c:06:68:e8:69 brd ff:ff:ff:ff:ff:ff
~/daq$ <b>ip link show pri-eth10</b>
2219: pri-eth10@if2218: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master ovs-system state UP mode DEFAULT group default qlen 1000
    link/ether a6:f5:1c:87:17:13 brd ff:ff:ff:ff:ff:ff link-netnsid 3
~/daq$ <b>docker exec daq-gw01 ip link</b>
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2216: eth0@if2217: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default 
    link/ether 02:42:c0:a8:09:03 brd ff:ff:ff:ff:ff:ff link-netnsid 0
2218: gw01-eth0@if2219: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default qlen 1000
    link/ether fa:74:5a:d8:d9:ed brd ff:ff:ff:ff:ff:ff link-netnsid 0
</pre>

## Capture files

Some useful files.
* _activate.log_: Docker logs for container.
* _startup.pcap_: Packet capture before tests run (e.g. initial DHCP). Decode using `tcpdump -r`

<pre>
~/daq$ <b>find inst/gw01/ -type f</b>
inst/gw01/dhcp_monitor.txt
inst/gw01/nodes/gw01/tmp/dnsmasq.log
inst/gw01/nodes/gw01/tmp/startup.pcap
inst/gw01/nodes/gw01/activate.log
~/daq$ <b>find inst/run-port-01/ -type f</b>
&hellip;
inst/run-port-01/nodes/ping01/return_code.txt
inst/run-port-01/nodes/ping01/activate.log
inst/run-port-01/scans/monitor.pcap
inst/run-port-01/scans/startup.pcap
</pre>
