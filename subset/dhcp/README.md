# DHCP Tests

## General

The DHCP module only scans the test_ipaddr.pcap packet capture file. 
This is because the functional code included in ipaddr communicates with the openflow supported switch via the universal switch interface. 

Due to this, the DHCP module requires the ipaddr module to run successfully: 
- If the ipaddr module does not run then an exception will occur when the DHCP module is run. 
- If the ipaddr runs but is unsuccessful then the DHCP module will likely report each test to be failed.

## Tests

### connection.network.dhcp_short
- Reconnect device and check for DHCP request. 
#### Result Cases:
- PASS: A DHCP request has been received by the device after the port has been disconnected and connected.
- FAIL: No DHCP request has been received.

## Integrated Testing

To provide full test coverage for this module, a static IP is configured for the faux-2 interface.
By configuring a static IP and disabling dhclient no DHCP requests are sent on this device.

The IP used is <strong>10.20.0.7</strong>.
