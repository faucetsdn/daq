# Network testing

## test_network
The network tests inspect client NTP support and version.

### Note for test developers 
The functional test code is included in the `network_tests.py` file.

The connection.network.ntpv4 test reads packets from startup.pcap.

If the python code needs debugging, the pip module `scapy` is required (`pip install scapy`).

### connection.network.ntpv4 Test conditions
| Test ID |  Info | Pass | Fail | Skip |
|---|---|---|---|---|
| connection.network.ntpv4 | Are the received NTP packets using NTP v4? | NTP version is 4 | NTP version is not 4 | No NTP packets are received |

