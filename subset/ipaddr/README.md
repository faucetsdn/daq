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
### connection.dhcp.private_address
- Device supports all private address ranges.
#### Result Cases:
- PASS: A DHCP request was received for each private address range.
- FAIL: A DHCP request was not received for each private address range.
### connection.network.dhcp_change
- Device receives new IP address after IP change and port toggle.
#### Result Cases:
- PASS: Device received the new IP address.
- FAIL: Device did not receive the new IP address.
