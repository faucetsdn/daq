# Device 9a:02:57:1e:8f:01, *** Make *** *** Model ***

## Test Roles

|  Role  |      Name              | Status |
|--------|------------------------|--------|
|Operator| *** Operator Name *** |        |
|Approver| *** Approver Name *** |        |

## Test Iteration

| Test             |                        |
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

|Category|Result|
|---|---|
|Security|1/2|
|Other|1/2|
|Connectivity|n/a|

|Expectation|pass|fail|skip|info|gone|
|---|---|---|---|---|---|
|Required|1|0|0|0|0|
|Recommended|1|0|0|0|1|
|Other|6|2|21|1|2|

|Result|Test|Category|Expectation|Notes|
|---|---|---|---|---|
|pass|base.startup.dhcp|Other|Other||
|skip|base.switch.ping|Other|Other|No local IP has been set, check system config|
|pass|base.target.ping|Connectivity|Required|target reached|
|skip|cloud.udmi.pointset|Other|Other|No device id|
|skip|cloud.udmi.state|Other|Other|No device id|
|skip|cloud.udmi.system|Other|Other|No device id|
|info|communication.type.broadcast|Other|Other|Broadcast packets received. Unicast packets received.|
|skip|connection.dns.hostname_connect|Other|Other|Device did not send any DNS requests|
|fail|connection.mac_oui|Other|Other|Manufacturer prefix not found!|
|pass|connection.min_send|Other|Other|ARP packets received. Data packets were sent at a frequency of less than 5 minutes|
|pass|connection.network.ntp_support|Other|Other|Using NTPv4.|
|pass|connection.network.ntp_update|Other|Other|Device clock synchronized.|
|skip|connection.port_duplex|Other|Other|No local IP has been set, check system config|
|skip|connection.port_link|Other|Other|No local IP has been set, check system config|
|skip|connection.port_speed|Other|Other|No local IP has been set, check system config|
|pass|manual.test.name|Security|Recommended|Manual test - for testing|
|skip|poe.switch.power|Other|Other|No local IP has been set, check system config|
|fail|protocol.bacnet.pic|Other|Other|PICS file defined however a BACnet device was not found.|
|skip|protocol.bacnet.version|Other|Other|Bacnet device not found.|
|skip|security.firmware|Other|Other|Could not retrieve a firmware version with nmap. Check bacnet port.|
|pass|security.nmap.http|Other|Other|No running http servers have been found.|
|pass|security.nmap.ports|Other|Other|Only allowed ports found open.|
|skip|security.passwords.http|Other|Other|Port 80 not open on target device.|
|skip|security.passwords.https|Other|Other|Port 443 not open on target device.|
|skip|security.passwords.ssh|Other|Other|Port 22 not open on target device.|
|skip|security.passwords.telnet|Other|Other|Port 23 not open on target device.|
|gone|security.ports.nmap|Security|Recommended||
|skip|security.tls.v1|Other|Other|IOException unable to connect to server|
|skip|security.tls.v1.x509|Other|Other|IOException unable to connect to server|
|skip|security.tls.v1_2|Other|Other|IOException unable to connect to server|
|skip|security.tls.v1_2.x509|Other|Other|IOException unable to connect to server|
|skip|security.tls.v1_3|Other|Other|IOException unable to connect to server|
|skip|security.tls.v1_3.x509|Other|Other|IOException unable to connect to server|
|gone|unknown.fake.llama|Other|Other||
|gone|unknown.fake.monkey|Other|Other||


## Module pass


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
base.target.ping
--------------------
Attempt to ping the Device Under Test
--------------------
See log above
--------------------
RESULT pass base.target.ping target reached

```

## Module nmap


#### Report

```
--------------------
security.nmap.ports
--------------------
Automatic TCP/UDP port scan using nmap
--------------------
# Nmap 7.60 scan initiated XXX as: nmap -v -n -T5 -sT -sU --host-timeout=4m --open -pU:47808,T:23,443,80, -oG /tmp/nmap.log X.X.X.X
# Ports scanned: TCP(3;23,80,443) UDP(1;47808) SCTP(0;) PROTOCOLS(0;)
Host: X.X.X.X ()	Status: Up
Host: X.X.X.X ()	Ports: 47808/closed/udp//bacnet///	
# Nmap done at XXX -- 1 IP address (1 host up) scanned in XXX
No invalid ports found.
--------------------
RESULT pass security.nmap.ports Only allowed ports found open.

--------------------
security.nmap.http
--------------------
Check that the device does not have open ports exposing an unencrypted web interface using HTTP
--------------------
# Nmap 7.60 scan initiated XXX as: nmap -v -n -T5 -A --script http-methods --host-timeout=4m --open -p- -oG /tmp/http.log X.X.X.X
# Ports scanned: TCP(65535;1-65535) UDP(0;) SCTP(0;) PROTOCOLS(0;)
Host: X.X.X.X ()	Status: Up
Host: X.X.X.X ()	Ports: 10000/open/tcp//snet-sensor-mgmt?///	
# Nmap done at XXX -- 1 IP address (1 host up) scanned in XXX
No running http servers have been found.
--------------------
RESULT pass security.nmap.http No running http servers have been found.

```

#### Module Config

|Attribute|Value|
|---|---|
|timeout_sec|600|
|enabled|True|

## Module discover


#### Report

```
--------------------
security.firmware
--------------------
Automatic bacnet firmware scan using nmap
--------------------
PORT      STATE  SERVICE
47808/udp closed bacnet
MAC Address: 9A:02:57:1E:8F:01 (Unknown)
--------------------
RESULT skip security.firmware Could not retrieve a firmware version with nmap. Check bacnet port.

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Module switch


#### Report

```
--------------------
connection.port_link
--------------------
Connect the device to the network switch. Check the device and the switch for the green connection light & no errors
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip connection.port_link No local IP has been set, check system config

--------------------
connection.port_speed
--------------------
Verify the device auto-negotiates connection speed
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip connection.port_speed No local IP has been set, check system config

--------------------
connection.port_duplex
--------------------
Verify the device supports full duplex
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip connection.port_duplex No local IP has been set, check system config

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
|poe|{'enabled': True}|

## Module bacext


#### Report

```
--------------------
protocol.bacnet.version
--------------------
Verify and record version of Bacnet used by the device
--------------------
 Bacnet device not found.
--------------------
RESULT skip protocol.bacnet.version Bacnet device not found.

--------------------
protocol.bacnet.pic
--------------------
Verify BACnet traffic is compliant to the PIC statement
--------------------
PICS file defined however a BACnet device was not found.
--------------------
RESULT fail protocol.bacnet.pic PICS file defined however a BACnet device was not found.

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

--------------------
security.tls.v1
--------------------
Verify the device supports TLS 1.0 (as a client)
--------------------
See log above
--------------------
RESULT skip security.tls.v1 IOException unable to connect to server

--------------------
security.tls.v1.x509
--------------------
Verify the devices supports RFC 2459 - Internet X.509 Public Key Infrastructure Certificate and CRL Profile
--------------------
See log above
--------------------
RESULT skip security.tls.v1.x509 IOException unable to connect to server

--------------------
security.tls.v1_2
--------------------
Verify the device supports TLS 1.2 (as a client)
--------------------
See log above
--------------------
RESULT skip security.tls.v1_2 IOException unable to connect to server

--------------------
security.tls.v1_2.x509
--------------------
null
--------------------
See log above
--------------------
RESULT skip security.tls.v1_2.x509 IOException unable to connect to server

--------------------
security.tls.v1_3
--------------------
Verify the device supports TLS 1.3 (as a client)
--------------------
See log above
--------------------
RESULT skip security.tls.v1_3 IOException unable to connect to server

--------------------
security.tls.v1_3.x509
--------------------
Verify the devices supports RFC 2459 - Internet X.509 Public Key Infrastructure Certificate and CRL Profile
--------------------
See log above
--------------------
RESULT skip security.tls.v1_3.x509 IOException unable to connect to server

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

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
RESULT skip security.passwords.http Port 80 not open on target device.

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
RESULT skip security.passwords.https Port 443 not open on target device.

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
RESULT skip security.passwords.ssh Port 22 not open on target device.

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
RESULT skip security.passwords.telnet Port 23 not open on target device.

```

#### Module Config

|Attribute|Value|
|---|---|
|dictionary_dir|resources/faux|
|enabled|True|

## Module udmi


#### Report

```
--------------------
cloud.udmi.state
--------------------
Validates device state payload.
--------------------
No device id
--------------------
RESULT skip cloud.udmi.state No device id

--------------------
cloud.udmi.pointset
--------------------
Validates device pointset payload.
--------------------
No device id
--------------------
RESULT skip cloud.udmi.pointset No device id

--------------------
cloud.udmi.system
--------------------
Validates device system payload.
--------------------
No device id
--------------------
RESULT skip cloud.udmi.system No device id

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Module manual


#### Report

```
--------------------
manual.test.name
--------------------

--------------------
No additional information provided
--------------------
RESULT pass manual.test.name Manual test - for testing

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Module network


#### Report

```
--------------------
connection.min_send
--------------------
Device sends data at a frequency of less than 5 minutes.
--------------------











RESULT pass connection.min_send ARP packets received. Data packets were sent at a frequency of less than 5 minutes
--------------------
communication.type.broadcast
--------------------
Device sends unicast or broadcast packets.
--------------------


RESULT info communication.type.broadcast Broadcast packets received. Unicast packets received.
--------------------
connection.network.ntp_support
--------------------
Device supports NTP version 4.
--------------------
RESULT pass connection.network.ntp_support Using NTPv4.
--------------------
connection.network.ntp_update
--------------------
Device synchronizes its time to the NTP server.
--------------------
RESULT pass connection.network.ntp_update Device clock synchronized.
--------------------
connection.mac_oui
--------------------
Check Physical device address OUI against IEEE registration and verify it is registered with the correct manufacturer
--------------------
Using the host hardware address 9a:02:57:1e:8f:01
Mac OUI Test
--------------------
RESULT fail connection.mac_oui Manufacturer prefix not found!

--------------------
connection.dns.hostname_connect
--------------------
Check device uses the DNS server from DHCP and resolves hostnames
--------------------
RESULT skip connection.dns.hostname_connect Device did not send any DNS requests
```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Report complete

