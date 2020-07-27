# NTP testing

## test_ntp
The NTP test inspects client NTP support and version.

### Note for test developers 
The functional test code is included in the `ntp_tests.py` file.

The test reads packets from startup.pcap.

If the python code needs debugging, the pip module `scapy` is required (`pip install scapy`).

### NTP Test conditions
| Test ID |  Info | Pass | Fail | Skip |
|---|---|---|---|---|
| connection.network.ntp_support | Are the received NTP packets using NTP v4? | NTP version is 4 | NTP version is not 4 | No NTP packets are received |

