# Device 9a:02:57:1e:8f:01, *** Make *** *** Model ***

## Test Roles

|  Role  |      Name              | Status |
|--------|------------------------|--------|
|Operator| *** Operator Name *** |        |
|Approver| *** Approver Name *** |        |

## Test Iteration

| Test parameter   | Value                  |
|------------------|------------------------|
| Test report start date | XXX |
| Test report end date   | XXX |
|
| Attempt number   | 1 |

## Device Identification

| Device            | Entry              |
|-------------------|--------------------|
| Name              | *** Name *** |
| GUID              | *** GUID *** |
| MAC addr          | 9a:02:57:1e:8f:01 |
| Hostname          | *** Network Hostname *** |
| Type              | *** Type *** |
| Make              | *** Make *** |
| Model             | *** Model *** |
| Serial Number     | *** Serial *** |
| Firmware Version  | *** Firmware Version *** |

## Device Description

![Image of device](*** Device Image URL ***)

*** Device Description ***


### Device documentation

[Device datasheets](*** Device Datasheets URL ***)
[Device manuals](*** Device Manuals URL ***)

## Report summary

Overall device result FAIL

**Some tests report as GONE. Please check for possible misconfiguration**

|Category|Total Tests|Result|Required Pass|Required Pass for PoE Devices|Required Pass for BACnet Devices|Required Pass for IoT Devices|Recommended Pass|Other|
|---|---|---|---|---|---|---|---|---|
|Base|2|FAIL|1/0/1|0/0/0|0/0/0|0/0/0|0/0/0|0/0/0|
|Connection|13|FAIL|4/5/4|0/0/0|0/0/0|0/0/0|0/0/0|0/0/0|
|Security|21|FAIL|3/8/7|0/0/0|0/0/1|0/0/0|0/0/2|0/0/0|
|NTP|2|PASS|2/0/0|0/0/0|0/0/0|0/0/0|0/0/0|0/0/0|
|DNS|1|SKIP|0/0/1|0/0/0|0/0/0|0/0/0|0/0/0|0/0/0|
|Communication|2|PASS|2/0/0|0/0/0|0/0/0|0/0/0|0/0/0|0/0/0|
|Protocol|2|FAIL|0/0/0|0/0/0|0/1/1|0/0/0|0/0/0|0/0/0|
|PoE|1|SKIP|0/0/0|0/0/1|0/0/0|0/0/0|0/0/0|0/0/0|
|IoT|1|SKIP|0/0/0|0/0/0|0/0/0|0/0/1|0/0/0|0/0/0|
|Other|2|GONE|0/0/0|0/0/0|0/0/0|0/0/0|0/0/0|0/2/0|
Syntax: Pass / Fail / Skip

|Expectation|pass|fail|skip|gone|
|---|---|---|---|---|
|Required Pass|12|8|13|5|
|Required Pass for PoE Devices|0|0|1|0|
|Required Pass for BACnet Devices|0|1|2|0|
|Required Pass for IoT Devices|0|0|1|0|
|Recommended Pass|0|0|2|0|
|Other|0|0|4|2|

|Result|Test|Category|Expectation|Notes|
|---|---|---|---|---|
|pass|base.startup.dhcp|Base|Required Pass||
|skip|base.switch.ping|Base|Required Pass|No local IP has been set, check system config|
|skip|cloud.udmi.event_pointset|IoT|Required Pass for IoT Devices|No device id|
|skip|cloud.udmi.event_system|Other|Other|No device id|
|skip|cloud.udmi.provision|Other|Other|No device id|
|skip|cloud.udmi.state_pointset|Other|Other|No device id|
|skip|cloud.udmi.state_system|Other|Other|No device id|
|pass|communication.network.min_send|Communication|Required Pass|ARP packets received. Data packets were sent at a frequency of less than 5 minutes|
|pass|communication.network.type|Communication|Required Pass|Broadcast packets received. Unicast packets received.|
|pass|connection.base.target_ping|Connection|Required Pass|target reached|
|pass|connection.dot1x.authentication|Connection|Required Pass|Authentication succeeded.|
|gone|connection.ipaddr.dhcp_disconnect|Connection|Required Pass||
|gone|connection.ipaddr.disconnect_ip_change|Connection|Required Pass||
|gone|connection.ipaddr.ip_change|Connection|Required Pass||
|gone|connection.ipaddr.private_address|Connection|Required Pass||
|pass|connection.manual.comms_down|Connection|Required Pass|Manual test - Device passed this manual test|
|skip|connection.manual.sec_eth_port|Connection|Required Pass|Manual test - Test results not inputted into module_config|
|pass|connection.network.mac_address|Connection|Required Pass|Device MAC address is 9a:02:57:1e:8f:01|
|fail|connection.network.mac_oui|Connection|Required Pass|Manufacturer prefix not found!|
|skip|connection.switch.port_duplex|Connection|Required Pass|No local IP has been set, check system config|
|skip|connection.switch.port_link|Connection|Required Pass|No local IP has been set, check system config|
|skip|connection.switch.port_speed|Connection|Required Pass|No local IP has been set, check system config|
|skip|dns.network.hostname_resolution|DNS|Required Pass|Device did not send any DNS requests|
|pass|ntp.network.ntp_support|NTP|Required Pass|Using NTPv4.|
|pass|ntp.network.ntp_update|NTP|Required Pass|Device clock synchronized.|
|skip|poe.switch.power|PoE|Required Pass for PoE Devices|No local IP has been set, check system config|
|fail|protocol.bacext.pic|Protocol|Required Pass for BACnet Devices|PICS file defined however a BACnet device was not found.|
|skip|protocol.bacext.version|Protocol|Required Pass for BACnet Devices|Bacnet device not found.|
|skip|security.discover.firmware|Security|Required Pass for BACnet Devices|Could not retrieve a firmware version with nmap. Check bacnet port.|
|pass|security.nmap.http|Security|Required Pass|No running http servers have been found.|
|fail|security.nmap.ports|Security|Required Pass|Some disallowed ports are open: 20,21,25,110,143,465,587,993,995,1256,5361,10000,21514,23451,69,161.|
|skip|security.password.http|Security|Required Pass|Port 80 not open on target device.|
|skip|security.password.https|Security|Required Pass|Port 443 not open on target device.|
|skip|security.password.ssh|Security|Required Pass|Port 22 not open on target device.|
|skip|security.password.telnet|Security|Required Pass|Port 23 not open on target device.|
|fail|security.services.ftp|Security|Required Pass|Service found running, ports found open|
|fail|security.services.imap|Security|Required Pass|Service found running, ports found open|
|fail|security.services.pop|Security|Required Pass|Service found running, ports found open|
|fail|security.services.smtp|Security|Required Pass|Service found running, ports found open|
|fail|security.services.snmpv3|Security|Required Pass|Port open and does not support SNMPv3|
|pass|security.services.telnet|Security|Required Pass|Only allowed ports found open.|
|fail|security.services.tftp|Security|Required Pass|Ports found open|
|pass|security.services.vnc|Security|Required Pass|Only allowed ports found open.|
|gone|security.ssh.version|Security|Required Pass||
|skip|security.tls.v1_2_client|Security|Required Pass|No client initiated TLS communication detected|
|skip|security.tls.v1_2_server|Security|Required Pass|IOException unable to connect to server.|
|skip|security.tls.v1_3_client|Security|Recommended Pass|No client initiated TLS communication detected|
|skip|security.tls.v1_3_server|Security|Recommended Pass|IOException unable to connect to server.|
|skip|security.tls.v1_server|Security|Required Pass|IOException unable to connect to server.|
|gone|unknown.fake.llama|Other|Other||
|gone|unknown.fake.monkey|Other|Other||


## Module pass


#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Module fail


#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Module ping


#### Report

```
--------------------
Baseline ping test report
LOCAL_IP not configured, assuming no network switch

Done with basic connectivity tests

--------------------
base.startup.dhcp
--------------------
Check the base DHCP startup exchange
--------------------
See log above
--------------------
RESULT pass base.startup.dhcp

--------------------
base.switch.ping
--------------------
Attempt to ping access switch (if configured)
--------------------
See log above
--------------------
RESULT skip base.switch.ping No local IP has been set, check system config

--------------------
connection.base.target_ping
--------------------
Attempt to ping the Device Under Test
--------------------
See log above
--------------------
RESULT pass connection.base.target_ping target reached

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Module nmap


#### Report

```
--------------------
security.nmap.ports
--------------------
Ensure disallowed ports are not open
--------------------
Port 20    (tcp)   open tcpwrapped
Port 21    (tcp)   open tcpwrapped
Port 25    (tcp)   open tcpwrapped
Port 69    (udp)   open tftp
Port 110   (tcp)   open tcpwrapped
Port 143   (tcp)   open tcpwrapped
Port 161   (udp)   open unknown
Port 465   (tcp)   open tcpwrapped
Port 587   (tcp)   open tcpwrapped
Port 993   (tcp)   open tcpwrapped
Port 995   (tcp)   open tcpwrapped
Port 1256  (tcp)   open smtp
Port 5361  (tcp)   open imap
Port 10000 (tcp)   open unknown
Port 21514 (tcp)   open ftp
Port 23451 (tcp)   open pop3
--------------------
RESULT fail security.nmap.ports Some disallowed ports are open: 20,21,25,110,143,465,587,993,995,1256,5361,10000,21514,23451,69,161.
--------------------
security.services.telnet
--------------------
Check TELNET port 23 is disabled and TELNET is not running on any port
--------------------

--------------------
RESULT pass security.services.telnet Only allowed ports found open.
--------------------
security.services.ftp
--------------------
Check FTP port 20/21 is disabled and FTP is not running on any port
--------------------
Port 20    (tcp)   open tcpwrapped
Port 21    (tcp)   open tcpwrapped
Port 21514 (tcp)   open ftp
--------------------
RESULT fail security.services.ftp Service found running, ports found open
--------------------
security.services.smtp
--------------------
Check SMTP port 25, 465, 587 are not open and SMTP is not running on any port
--------------------
Port 25    (tcp)   open tcpwrapped
Port 465   (tcp)   open tcpwrapped
Port 587   (tcp)   open tcpwrapped
Port 1256  (tcp)   open smtp
--------------------
RESULT fail security.services.smtp Service found running, ports found open
--------------------
security.services.imap
--------------------
Check IMAP port 143 is disabled and IMAP is not running on any port
--------------------
Port 143   (tcp)   open tcpwrapped
Port 993   (tcp)   open tcpwrapped
Port 5361  (tcp)   open imap
--------------------
RESULT fail security.services.imap Service found running, ports found open
--------------------
security.services.pop
--------------------
Check POP port 110 is disabled and POP is not running on any port
--------------------
Port 110   (tcp)   open tcpwrapped
Port 995   (tcp)   open tcpwrapped
Port 23451 (tcp)   open pop3
--------------------
RESULT fail security.services.pop Service found running, ports found open
--------------------
security.services.vnc
--------------------
Check VNC is disabled on any port
--------------------

--------------------
RESULT pass security.services.vnc Only allowed ports found open.
--------------------
security.services.tftp
--------------------
Check TFTP port 69 is disabled (UDP)
--------------------
Port 69    (udp)   open tftp
--------------------
RESULT fail security.services.tftp Ports found open
--------------------
security.services.snmpv3
--------------------
Check SNMP port 161/162 is disabled. If SNMP is an essential service, check it supports version 3
--------------------
Port 161   (udp)   open unknown
--------------------
RESULT fail security.services.snmpv3 Port open and does not support SNMPv3
--------------------
security.nmap.http
--------------------
Check that the device does not have open ports exposing an unencrypted web interface using HTTP
--------------------
# Nmap XXX scan initiated XXX as: nmap -v -n -T3 -A --script http-methods --host-timeout=4m --open -p- -oG XXX/tmp/http.log X.X.X.X
# Ports scanned: TCP(65535;1-65535) UDP(0;) SCTP(0;) PROTOCOLS(0;)
Host: X.X.X.X () Status: Up
Host: X.X.X.X () Ports: 1256/open/tcp//smtp//Postfix smtpd/, 5361/open/tcp//imap//Dovecot imapd (Ubuntu)/, 10000/open/tcp//snet-sensor-mgmt?///, 21514/open/tcp//ftp//ProFTPD 1.3.5e/, 23451/open/tcp//pop3//zpop3d/
# Nmap done at XXX -- 1 IP address (1 host up) scanned in XXX
No running http servers have been found.
--------------------
RESULT pass security.nmap.http No running http servers have been found.

```

#### Module Config

|Attribute|Value|
|---|---|
|timeout_sec|900|
|enabled|True|

## Module discover


#### Report

```
--------------------
security.discover.firmware
--------------------
Automatic bacnet firmware scan using nmap
--------------------
PORT      STATE  SERVICE
47808/udp closed bacnet
MAC Address: 9A:02:57:1E:8F:01 (Unknown)
--------------------
RESULT skip security.discover.firmware Could not retrieve a firmware version with nmap. Check bacnet port.

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Module switch


#### Report

```
--------------------
connection.switch.port_link
--------------------
Connect the device to the network switch. Check the device and the switch for the green connection light & no errors
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip connection.switch.port_link No local IP has been set, check system config

--------------------
connection.switch.port_speed
--------------------
Verify the device auto-negotiates connection speed
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip connection.switch.port_speed No local IP has been set, check system config

--------------------
connection.switch.port_duplex
--------------------
Verify the device supports full duplex
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip connection.switch.port_duplex No local IP has been set, check system config

--------------------
poe.switch.power
--------------------
Verify that the device draws less than the maximum power allocated by the port. This is 15.4W for 802.3af and 30W for 802.3at
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip poe.switch.power No local IP has been set, check system config

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|
|timeout_sec|0|
|poe|{'enabled': True}|

## Module bacext


#### Report

```
--------------------
protocol.bacext.version
--------------------
Verify and record version of Bacnet used by the device
--------------------
 Bacnet device not found.
--------------------
RESULT skip protocol.bacext.version Bacnet device not found.

--------------------
protocol.bacext.pic
--------------------
Verify BACnet traffic is compliant to the PIC statement
--------------------
PICS file defined however a BACnet device was not found.
--------------------
RESULT fail protocol.bacext.pic PICS file defined however a BACnet device was not found.

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Module tls


#### Report

```
--------------------
Collecting TLS cert from target address

Gathering TLS 1 Server Information....
TLS 1Server Implementation Skipping Test, could not open connection
TLS 1 Server Information Complete.


Gathering TLS 1.2 Server Information....
TLS 1.2Server Implementation Skipping Test, could not open connection
TLS 1.2 Server Information Complete.


Gathering TLS 1.3 Server Information....
TLS 1.3Server Implementation Skipping Test, could not open connection
TLS 1.3 Server Information Complete.


Gathering TLS Client X.X.X.X Information....
TLS Client Information Complete.
Gathering TLS Client X.X.X.X Information....
TLS Client Information Complete.

--------------------
security.tls.v1_2_client
--------------------
Verify the device supports at least TLS 1.2 (as a client)
--------------------
See log above
--------------------
RESULT skip security.tls.v1_2_client No client initiated TLS communication detected

--------------------
security.tls.v1_2_server
--------------------
Verify the device supports TLS 1.2 (as a server)
--------------------
See log above
--------------------
RESULT skip security.tls.v1_2_server IOException unable to connect to server.

--------------------
security.tls.v1_3_client
--------------------
Verify the device supports at least TLS 1.3 (as a client)
--------------------
See log above
--------------------
RESULT skip security.tls.v1_3_client No client initiated TLS communication detected

--------------------
security.tls.v1_3_server
--------------------
Verify the device supports TLS 1.3 (as a server)
--------------------
See log above
--------------------
RESULT skip security.tls.v1_3_server IOException unable to connect to server.

--------------------
security.tls.v1_server
--------------------
Verify the device supports at least TLS 1.0 (as a server)
--------------------
See log above
--------------------
RESULT skip security.tls.v1_server IOException unable to connect to server.

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|
|timeout_sec|0|
|ca_file|CA_Faux.pem|

## Module password


#### Report

```
--------------------
security.admin.password.http
--------------------
Verify all device manufacturer default passwords are changed for protocol: http, and new passwords are set.
--------------------

Starting Nmap 7.60 ( https://nmap.org ) at XXX
Nmap scan report for daq-faux-1 (X.X.X.X)
Host is up (XXX).

PORT   STATE  SERVICE
80/tcp closed http
MAC Address: 9A:02:57:1E:8F:01 (Unknown)

Nmap done: 1 IP address (1 host up) scanned in XXX
Could not connect to specified port on host.
--------------------
RESULT skip security.password.http Port 80 not open on target device.

--------------------
security.admin.password.https
--------------------
Verify all device manufacturer default passwords are changed for protocol: https, and new passwords are set.
--------------------

Starting Nmap 7.60 ( https://nmap.org ) at XXX
Nmap scan report for daq-faux-1 (X.X.X.X)
Host is up (XXX).

PORT    STATE  SERVICE
443/tcp closed https
MAC Address: 9A:02:57:1E:8F:01 (Unknown)

Nmap done: 1 IP address (1 host up) scanned in XXX
Could not connect to specified port on host.
--------------------
RESULT skip security.password.https Port 443 not open on target device.

--------------------
security.admin.password.ssh
--------------------
Verify all device manufacturer default passwords are changed for protocol: ssh, and new passwords are set.
--------------------

Starting Nmap 7.60 ( https://nmap.org ) at XXX
Nmap scan report for daq-faux-1 (X.X.X.X)
Host is up (XXX).

PORT   STATE  SERVICE
22/tcp closed ssh
MAC Address: 9A:02:57:1E:8F:01 (Unknown)

Nmap done: 1 IP address (1 host up) scanned in XXX
Could not connect to specified port on host.
--------------------
RESULT skip security.password.ssh Port 22 not open on target device.

--------------------
security.admin.password.telnet
--------------------
Verify all device manufacturer default passwords are changed for protocol: telnet, and new passwords are set.
--------------------

Starting Nmap 7.60 ( https://nmap.org ) at XXX
Nmap scan report for daq-faux-1 (X.X.X.X)
Host is up (XXX).

PORT   STATE  SERVICE
23/tcp closed telnet
MAC Address: 9A:02:57:1E:8F:01 (Unknown)

Nmap done: 1 IP address (1 host up) scanned in XXX
Could not connect to specified port on host.
--------------------
RESULT skip security.password.telnet Port 23 not open on target device.

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|
|timeout_sec|0|
|dictionary_dir|resources/faux|

## Module udmi


#### Report

```
--------------------
cloud.udmi.provision
--------------------
Validates device provision payload.
--------------------
No device id
--------------------
RESULT skip cloud.udmi.provision No device id

--------------------
cloud.udmi.state_system
--------------------
Validates device state_system payload.
--------------------
No device id
--------------------
RESULT skip cloud.udmi.state_system No device id

--------------------
cloud.udmi.state_pointset
--------------------
Validates device state_pointset payload.
--------------------
No device id
--------------------
RESULT skip cloud.udmi.state_pointset No device id

--------------------
cloud.udmi.event_system
--------------------
Validates device event_system payload.
--------------------
No device id
--------------------
RESULT skip cloud.udmi.event_system No device id

--------------------
cloud.udmi.event_pointset
--------------------
Validates device event_pointset payload.
--------------------
No device id
--------------------
RESULT skip cloud.udmi.event_pointset No device id

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Module manual


#### Report

```
--------------------
connection.manual.comms_down
--------------------

--------------------
No additional information provided
--------------------
RESULT pass connection.manual.comms_down Manual test - Device passed this manual test

--------------------
connection.manual.sec_eth_port
--------------------

--------------------
No additional information provided
--------------------
RESULT skip connection.manual.sec_eth_port Manual test - Test results not inputted into module_config

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Module network


#### Report

```
--------------------
communication.network.min_send
--------------------
Device sends data at a frequency of less than 5 minutes.
--------------------
RESULT pass communication.network.min_send ARP packets received. Data packets were sent at a frequency of less than 5 minutes
--------------------
communication.network.type
--------------------
Device sends unicast or broadcast packets.
--------------------
RESULT pass communication.network.type Broadcast packets received. Unicast packets received.
--------------------
ntp.network.ntp_support
--------------------
Device supports NTP version 4.
--------------------
RESULT pass ntp.network.ntp_support Using NTPv4.
--------------------
ntp.network.ntp_update
--------------------
Device synchronizes its time to the NTP server.
--------------------
RESULT pass ntp.network.ntp_update Device clock synchronized.
--------------------
connection.network.mac_oui
--------------------
Check Physical device address OUI against IEEE registration and verify it is registered with the correct manufacturer
--------------------
Using the host hardware address 9a:02:57:1e:8f:01
Mac OUI Test
--------------------
RESULT fail connection.network.mac_oui Manufacturer prefix not found!

--------------------
connection.network.mac_address
--------------------
Reports device MAC address
--------------------
Device MAC address is 9a:02:57:1e:8f:01
--------------------
RESULT pass connection.network.mac_address Device MAC address is 9a:02:57:1e:8f:01

--------------------
dns.network.hostname_resolution
--------------------
Check device uses the DNS server from DHCP and resolves hostnames
--------------------
RESULT skip dns.network.hostname_resolution Device did not send any DNS requests
```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Module dot1x


#### Report

```
--------------------
connection.dot1x.authentication
--------------------
Verifies general support for 802.1x authentication.
--------------------
--------------------
RESULT pass connection.dot1x.authentication Authentication succeeded.

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Report complete

