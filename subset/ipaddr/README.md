# DHCP Tests

## General

The ipaddr module is triggered by native ipaddr test.
This is because the functional code included in ipaddr communicates with the openflow supported switch via the universal switch interface. This module analyzes the output of the ipaddr in the tmp/activate.log file for DHCP activity.

## Tests

### connection.network.dhcp_short
- Reconnect device and check for DHCP request. 
#### Result Cases:
- PASS: A DHCP request has been received by the device after the port has been disconnected and connected.
- FAIL: No DHCP request was received (this will also be the case if the target is using a static IP).

### connection.dhcp.ip_change
- Device communicates after IP change.
#### Result Cases:
- PASS: A ping reply is found after the IP address has been changed.
- FAIL: No ping reply is found after the IP address has been changed.
