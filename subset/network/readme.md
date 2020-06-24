# Network Module

## connection.dhcp_long
- Located in network_tests.py, started up in test_network.
- The aim of the test is to check that the device issues a DHCPREQUEST after having been disconnected and after the DHCP lease has expired.

### Testing procedure:
- Runs a tcpdump command check if any ARP packets are being sent.
- PASS: If packets are found from the tcpdump scan.
- FAIL: If packets are not found from the tcpdump scan.

## connection.min_send
- Located in network_tests.py, started up in test_network.
- Check if a device sends any data packet at a frequency of less than five minutes.

### Result cases:
- PASS: The time between packets is measured - pass if time between any two packets is less than five minutes (deals with case where a monitor scan is long)
- FAIL: If data packets are sent, and there are packets with time interval of less than five minutes found, then fail.
- SKIP: If no data packets are sent and the monitor scan period is short, the test will skip instead of failing.

## communication.type.broadcast
- Located in network_tests.py, started up in test_network.
- This test counts the number of unicast, broadcast and multicast packets sent out by reading from the .pcap file that DAQ has created during runtime.

### Testing procedure:
1. Run tcpdump command to find broadcast packets coming from the specified source address.
2. To get the number of broadcast packets, it counts the lines from the tcpdump output. Add this to the final report.
3. Run tcpdump command again to find multicast packets with the first byte of their addresses that are between 224 to 239 inclusive.
4. To get the number of multicast packets, it counts the lines from the tcpdump output. Add this to the final report.
5. Run the tcpdump again but to find all packets sent.
6. To get the number of unicast packets, subtract the number of broadcast and multicast packets if any, from the unicast packet count, and add to the report.

### Result cases:
This is an 'info' test, it does not have a pass/fail/skip case.

## network.ntp.support
- Located in network_tests.py, started up in test_network.
- Does the device support: RFC 5905 - Network Time Protocol Version 4: Protocol and Algorithms Specification

### Testing procedure:
- Runs a tcpdump command check if any packets are being sent to a destination port of 123.
- PASS: If packets are found from the tcpdump scan.
- FAIL: If packets are not found from the tcpdump scan.