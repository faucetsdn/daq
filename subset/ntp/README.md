# NTP testing

## test_ntp
The NTP tests inspect the client NTP version and the device's ability to update its clock precisely.

### Note for test developers 
The functional test code is included in the `ntp_tests.py` file.

The test reads packets from startup.pcap.

If the python code needs debugging, the pip module `scapy` is required (`pip install scapy`).

### NTP Test conditions
| Test ID |  Info | Pass | Fail | Skip |
|---|---|---|---|---|
| connection.network.ntp_support | Are the received NTP packets using NTP v4? | NTP version is 4 | NTP version is not 4 | No NTP packets are received |
| connection.network.ntp_update | Does the device demonstrate updating its clock using NTP? | Device clock is synchronized | Device clock is not synchronized | Not enough NTP packets are received |
