# NTP testing

## test_ntp
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
