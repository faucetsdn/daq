<pre>
<b>~/daq$ tcpdump -en -r inst/run-port-01/nodes/gw01/tmp/startup.pcap ip</b>
reading from file inst/run-port-01/nodes/gw01/tmp/startup.pcap, link-type EN10MB (Ethernet)
22:04:40.807703 3a:4c:a1:35:80:e1 > 12:3b:a5:63:ae:04, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.0.0.2: ICMP echo request, id 24, seq 1, length 64
22:04:40.808146 12:3b:a5:63:ae:04 > 3a:4c:a1:35:80:e1, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 24, seq 1, length 64
22:04:41.807368 3a:4c:a1:35:80:e1 > 12:3b:a5:63:ae:04, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.0.0.2: ICMP echo request, id 24, seq 2, length 64
22:04:41.807438 12:3b:a5:63:ae:04 > 3a:4c:a1:35:80:e1, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 24, seq 2, length 64
22:04:41.815104 12:3b:a5:63:ae:04 > 3a:4c:a1:35:80:e1, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 10.0.0.1: ICMP echo request, id 56237, seq 1, length 64
22:04:41.815169 3a:4c:a1:35:80:e1 > 12:3b:a5:63:ae:04, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.0.0.2: ICMP echo reply, id 56237, seq 1, length 64
22:04:42.847264 12:3b:a5:63:ae:04 > 3a:4c:a1:35:80:e1, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 10.0.0.1: ICMP echo request, id 56237, seq 2, length 64
22:04:42.847301 3a:4c:a1:35:80:e1 > 12:3b:a5:63:ae:04, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.0.0.2: ICMP echo reply, id 56237, seq 2, length 64
22:04:42.854500 12:3b:a5:63:ae:04 > 3a:4c:a1:35:80:e1, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 192.168.84.72: ICMP echo request, id 56240, seq 1, length 64
22:04:42.854550 3a:4c:a1:35:80:e1 > 12:3b:a5:63:ae:04, ethertype IPv4 (0x0800), length 98: 192.168.84.72 > 10.0.0.2: ICMP echo reply, id 56240, seq 1, length 64
22:04:43.871383 12:3b:a5:63:ae:04 > 3a:4c:a1:35:80:e1, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 192.168.84.72: ICMP echo request, id 56240, seq 2, length 64
22:04:43.871421 3a:4c:a1:35:80:e1 > 12:3b:a5:63:ae:04, ethertype IPv4 (0x0800), length 98: 192.168.84.72 > 10.0.0.2: ICMP echo reply, id 56240, seq 2, length 64
22:04:43.877593 3a:4c:a1:35:80:e1 > 12:3b:a5:63:ae:04, ethertype IPv4 (0x0800), length 98: 192.168.84.72 > 10.0.0.2: ICMP echo request, id 25, seq 1, length 64
22:04:43.877668 12:3b:a5:63:ae:04 > 3a:4c:a1:35:80:e1, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 192.168.84.72: ICMP echo reply, id 25, seq 1, length 64
22:04:44.219881 ce:d3:e6:e4:1f:79 > ff:ff:ff:ff:ff:ff, ethertype IPv4 (0x0800), length 342: 0.0.0.0.68 > 255.255.255.255.67: BOOTP/DHCP, Request from ce:d3:e6:e4:1f:79, length 300
22:04:44.895211 3a:4c:a1:35:80:e1 > 12:3b:a5:63:ae:04, ethertype IPv4 (0x0800), length 98: 192.168.84.72 > 10.0.0.2: ICMP echo request, id 25, seq 2, length 64
22:04:44.895285 12:3b:a5:63:ae:04 > 3a:4c:a1:35:80:e1, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 192.168.84.72: ICMP echo reply, id 25, seq 2, length 64
22:04:47.150151 3a:4c:a1:35:80:e1 > ce:d3:e6:e4:1f:79, ethertype IPv4 (0x0800), length 62: 10.0.0.1 > 10.20.72.57: ICMP echo request, id 27415, seq 0, length 28
22:04:47.150347 3a:4c:a1:35:80:e1 > ce:d3:e6:e4:1f:79, ethertype IPv4 (0x0800), length 342: 10.0.0.1.67 > 10.20.72.57.68: BOOTP/DHCP, Reply, length 300
22:04:47.155721 ce:d3:e6:e4:1f:79 > ff:ff:ff:ff:ff:ff, ethertype IPv4 (0x0800), length 342: 0.0.0.0.68 > 255.255.255.255.67: BOOTP/DHCP, Request from ce:d3:e6:e4:1f:79, length 300
22:04:47.161834 3a:4c:a1:35:80:e1 > ce:d3:e6:e4:1f:79, ethertype IPv4 (0x0800), length 348: 10.0.0.1.67 > 10.20.72.57.68: BOOTP/DHCP, Reply, length 306
22:05:07.251289 3a:4c:a1:35:80:e1 > ce:d3:e6:e4:1f:79, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.20.72.57: ICMP echo request, id 32, seq 1, length 64
22:05:07.252329 ce:d3:e6:e4:1f:79 > 3a:4c:a1:35:80:e1, ethertype IPv4 (0x0800), length 98: 10.20.72.57 > 10.0.0.1: ICMP echo reply, id 32, seq 1, length 64
22:05:08.252844 3a:4c:a1:35:80:e1 > ce:d3:e6:e4:1f:79, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.20.72.57: ICMP echo request, id 32, seq 2, length 64
22:05:08.252923 ce:d3:e6:e4:1f:79 > 3a:4c:a1:35:80:e1, ethertype IPv4 (0x0800), length 98: 10.20.72.57 > 10.0.0.1: ICMP echo reply, id 32, seq 2, length 64
22:05:08.260403 3a:4c:a1:35:80:e1 > ce:d3:e6:e4:1f:79, ethertype IPv4 (0x0800), length 98: 192.168.84.72 > 10.20.72.57: ICMP echo request, id 33, seq 1, length 64
22:05:08.260512 ce:d3:e6:e4:1f:79 > 3a:4c:a1:35:80:e1, ethertype IPv4 (0x0800), length 98: 10.20.72.57 > 192.168.84.72: ICMP echo reply, id 33, seq 1, length 64
22:05:09.279288 3a:4c:a1:35:80:e1 > ce:d3:e6:e4:1f:79, ethertype IPv4 (0x0800), length 98: 192.168.84.72 > 10.20.72.57: ICMP echo request, id 33, seq 2, length 64
22:05:09.279402 ce:d3:e6:e4:1f:79 > 3a:4c:a1:35:80:e1, ethertype IPv4 (0x0800), length 98: 10.20.72.57 > 192.168.84.72: ICMP echo reply, id 33, seq 2, length 64
22:05:12.381259 ce:d3:e6:e4:1f:79 > fa:ae:23:61:d8:89, ethertype IPv4 (0x0800), length 98: 10.20.72.57 > 10.0.0.5: ICMP echo reply, id 17, seq 1, length 64
</pre>