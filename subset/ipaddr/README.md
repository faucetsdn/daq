# DHCP Tests

## General

The ipaddr module is triggered by native ipaddr test.
This is because the functional code included in ipaddr communicates with the openflow supported switch via the universal switch interface. This module analyzes the output of the ipaddr in the tmp/activate.log file for DHCP activity.

## Tests

### connection.ipaddr.dhcp_disconnect
- Reconnect device and check for DHCP request. 
#### Result Cases:
- PASS: A DHCP request has been received by the device after the port has been disconnected and connected.
- FAIL: No DHCP request was received (this will also be the case if the target is using a static IP).

### connection.ipaddr.private_address
- Device supports all private address ranges.
#### Result Cases:
- PASS: A DHCP request was received for each private address range.
- FAIL: A DHCP request was not received for each private address range.

### connection.ipaddr.disconnect_ip_change
- Device receives new IP address after IP change and port toggle.
#### Result Cases:
- PASS: Device received the new IP address.
- FAIL: Device did not receive the new IP address.

### connection.ipaddr.ip_change
- Device communicates after IP change.
#### Result Cases:
- PASS: A ping reply is found after the IP address has been changed.
- FAIL: No ping reply is found after the IP address has been changed.
