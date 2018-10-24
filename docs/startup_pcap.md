# Startup Sequence PCAP

Before a device is considered "active", it needs to perform basic network functions such as DHCP and ARP lookups.
The network traffic from this phase is automatically caputed by the system and can be useful for debugging of
startup sequence errors with devices.

<pre>
~/daq$ <b>tcpdump -en -r inst/run-port-01/scans/startup.pcap port 67</b>
reading from file inst/run-port-01/scans/startup.pcap, link-type EN10MB (Ethernet)
17:09:47.329555 9a:02:57:1e:8f:01 > ff:ff:ff:ff:ff:ff, ethertype IPv4 (0x0800), length 342: 0.0.0.0.68 > 255.255.255.255.67: BOOTP/DHCP, Request from 9a:02:57:1e:8f:01, length 300
17:09:50.085602 6a:24:d4:4e:26:33 > 9a:02:57:1e:8f:01, ethertype IPv4 (0x0800), length 342: 10.0.0.1.67 > 10.20.32.162.68: BOOTP/DHCP, Reply, length 300
17:09:50.086504 9a:02:57:1e:8f:01 > ff:ff:ff:ff:ff:ff, ethertype IPv4 (0x0800), length 342: 0.0.0.0.68 > 255.255.255.255.67: BOOTP/DHCP, Request from 9a:02:57:1e:8f:01, length 300
17:09:50.095173 6a:24:d4:4e:26:33 > 9a:02:57:1e:8f:01, ethertype IPv4 (0x0800), length 346: 10.0.0.1.67 > 10.20.32.162.68: BOOTP/DHCP, Reply, length 304
</pre>