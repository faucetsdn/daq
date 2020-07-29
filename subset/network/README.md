# Network Tests

## General Network Tests

### connection.min_send
- Located in network_tests.py, started up in test_network.
- Check if a device sends any data packet at a frequency of less than five minutes.

#### Result cases:
- PASS: The time between packets is measured - pass if time between any two packets is less than five minutes (deals with case where a monitor scan is long)
- FAIL: If data packets are sent, and there are packets with time interval of less than five minutes found, then fail.
- SKIP: If no data packets are sent and the monitor scan period is short, the test will skip instead of failing.

### communication.type.broadcast
- Located in network_tests.py, started up in test_network.
- This test counts the number of unicast, broadcast and multicast packets sent out by reading from the .pcap file that DAQ has created during runtime.

#### Result cases:
This is an 'info' test, it does not have a pass/fail/skip case.


## NTP Tests
The NTP tests inspect the client NTP version and the device's ability to update its clock precisely.

### Note for test developers 
The functional test code is included in the `ntp_tests.py` file.

The test reads packets from startup.pcap and monitor.pcap.

If the python code needs debugging, the pip module `scapy` is required (`pip install scapy`).

### NTP Test conditions
| Test ID |  Info | Pass | Fail | Skip |
|---|---|---|---|---|
| connection.network.ntp_support | Are the received NTP packets using NTP v4? | NTP version is 4 | NTP version is not 4 | No NTP packets are received |
| connection.network.ntp_update | Does the device demonstrate updating its clock using NTP? | Device clock is synchronized | Device clock is not synchronized | Not enough NTP packets are received |

#### NTP Support ####
The version of NTP used by the client is extracted from the fist client (outbound) NTP packets discovered in startup.pcap.

#### NTP Update ####
The following criteria are used to determine whether a DUT has synced its clock with the NTP server provided by DAQ:
 - A minimum of 2 NTP packets are present in startup.pcap and monitor.pcap (one potential poll).
 - A minimum of 2 NTP packets have been exchanged between the DUT and the DAQ-provided NTP server.
 - A valid NTP poll is present. Consisting of a client-server exchange.
 - The calculated offset is less than 0.128 seconds and the final poll does not have a leap indicator of 3 (unsynchronized).

When calculating the offset, the latest valid poll is inspected. A value of 0.128s is the maximum offset used to determine whether a device is considered in-sync with the NTP server because NTPv4 is capable of accuracy of tens of milliseconds.


## MAC OUI
The MAC OUI test looks up the manufacturer information for the mac address of the device under test.

### Note for test developers 
The functional test code is included in the `mac_oui/src/main/java` folder.

The `macList.txt` file containing the MAC OUI database is downloaded at build time by the container specified in
the `Dockerfile.test_macoui` file.

If java code requires debugging in an IDE, then it will require the `macList.txt` to be placed under the 
`mac_oui/src/main/resources/` folder. Use the curl command from the `Dockerfile.test_macoui` file to download and 
place the file locally into your project. This `.txt` file is git ignored to avoid being included as a 
static resource on the source code repo.

### Conditions for mac_oui
 - pass -> if the MAC OUI matches the mac prefix IEEE registration.
 - fail -> if the MAC OUI does not match with any of the mac prefixes.
