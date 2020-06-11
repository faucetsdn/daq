# Network testing

## test_network
The network tests inspect client NTP support and version.

### Note for test developers 
The functional test code is included in the `network_tests.py` file.

The network.ntp.support test reads packets from monitor.pcap. The network.ntp.support_v4 test reads packets from startup.pcap.

If the python code needs debugging, the pip module `scapy` is required (`pip install scapy`).

### Test conditions
| Test ID |  Info | Pass | Fail | Skip |
|---|---|---|---|---|
| network.ntp.support | Does the DUT send NTP request packets? | NTP packets are received | No NTP packets are received |   |
| network.ntp.support_v4 | Are the received NTP packets using NTP v4? | NTP version is 4 | NTP version is not 4 | No NTP packets are received |

