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
|Security|PASS|
|Other|1/2|
|Connectivity|n/a|

|Expectation|pass|fail|skip|gone|
|---|---|---|---|---|
|Required|1|0|0|0|
|Recommended|2|0|0|0|
|Other|1|2|22|2|

|Result|Test|Category|Expectation|Notes|
|---|---|---|---|---|
|pass|base.startup.dhcp|Other|Other||
|skip|base.switch.ping|Other|Other|No local IP has been set, check system config|
|pass|base.target.ping|Connectivity|Required|target reached|
|skip|cloud.udmi.pointset|Other|Other|No device id|
|skip|cloud.udmi.state|Other|Other|No device id|
|skip|cloud.udmi.system|Other|Other|No device id|
|fail|connection.mac_oui|Other|Other|Manufacturer prefix not found!|
|skip|connection.port_duplex|Other|Other|No local IP has been set, check system config|
|skip|connection.port_link|Other|Other|No local IP has been set, check system config|
|skip|connection.port_speed|Other|Other|No local IP has been set, check system config|
|pass|manual.test.travis|Security|Recommended|Manual test - for testing|
|skip|poe.negotiation|Other|Other|No local IP has been set, check system config|
|skip|poe.power|Other|Other|No local IP has been set, check system config|
|skip|poe.support|Other|Other|No local IP has been set, check system config|
|fail|protocol.bacnet.pic|Other|Other|PICS file defined however a BACnet device was not found.|
|skip|protocol.bacnet.version|Other|Other|Bacnet device not found.|
|skip|security.firmware|Other|Other|Could not retrieve a firmware version with nmap. Check bacnet port.|
|skip|security.passwords.http|Other|Other|Port 80 is not open on target device.|
|skip|security.passwords.https|Other|Other|Port 443 is not open on target device.|
|skip|security.passwords.ssh|Other|Other|Port 22 is not open on target device.|
|skip|security.passwords.telnet|Other|Other|Port 23 is not open on target device.|
|pass|security.ports.nmap|Security|Recommended|Only allowed ports found open.|
|skip|security.tls.v1|Other|Other|IOException unable to connect to server|
|skip|security.tls.v1.x509|Other|Other|IOException unable to connect to server|
|skip|security.tls.v1_2|Other|Other|IOException unable to connect to server|
|skip|security.tls.v1_2.x509|Other|Other|IOException unable to connect to server|
|skip|security.tls.v1_3|Other|Other|IOException unable to connect to server|
|skip|security.tls.v1_3.x509|Other|Other|IOException unable to connect to server|
|gone|unknown.fake.llama|Other|Other||
|gone|unknown.fake.monkey|Other|Other||


## Module ipaddr


#### Module Config

|Attribute|Value|
|---|---|
|timeout_sec|300|

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
security.ports.nmap
--------------------
Automatic TCP/UDP port scan using nmap
--------------------
# Nmap 7.60 scan initiated XXX as: nmap -v -n -T5 -sT -sU --host-timeout=4m --open -pU:47808,T:23,443,80, -oG /tmp/nmap.log X.X.X.X
# Ports scanned: TCP(3;23,80,443) UDP(1;47808) SCTP(0;) PROTOCOLS(0;)
Host: X.X.X.X ()	Status: Up
Host: X.X.X.X ()	Ports: 47808/closed/udp//bacnet///	Ignored State: closed (3)
# Nmap done at XXX -- 1 IP address (1 host up) scanned in XXX
No invalid ports found.
--------------------
RESULT pass security.ports.nmap Only allowed ports found open.

```

#### Module Config

|Attribute|Value|
|---|---|
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
poe.power
--------------------
Verify that the device draws less than the maximum power allocated by the port. This is 15.4W for 802.3af and 30W for 802.3at
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip poe.power No local IP has been set, check system config

--------------------
poe.negotiation
--------------------
Verify the device autonegotiates power requirements
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip poe.negotiation No local IP has been set, check system config

--------------------
poe.support
--------------------
Verify if the device supports PoE
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip poe.support No local IP has been set, check system config

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|
|poe|{'enabled': True}|

## Module macoui


#### Report

```
--------------------
connection.mac_oui
--------------------
Check Physical device address OUI against IEEE registration and verify it is registered with the correct manufacturer
--------------------
Using the host hardware address 9a:02:57:1e:8f:01
Mac OUI Test
--------------------
RESULT fail connection.mac_oui Manufacturer prefix not found!

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

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
security.passwords.http
--------------------
Verify all default passwords are updated and new Google provided passwords are set.
--------------------
[STARTING WITH IP:X.X.X.X, MAC:9a:02:57:1e:8f:01, PROTOCOL: http]
Starting NMAP check...

Starting Nmap 7.60 ( https://nmap.org ) at XXX
Nmap scan report for daq-faux-1 (X.X.X.X)
Host is up (XXX).

PORT      STATE SERVICE
10000/tcp open  snet-sensor-mgmt
MAC Address: 9A:02:57:1E:8F:01 (Unknown)

Nmap done: 1 IP address (1 host up) scanned in XXX
nmap X.X.X.X
Done.
--------------------
RESULT skip security.passwords.http Port 80 is not open on target device.

--------------------
security.passwords.https
--------------------
Verify all default passwords are updated and new Google provided passwords are set.
--------------------
[STARTING WITH IP:X.X.X.X, MAC:9a:02:57:1e:8f:01, PROTOCOL: https]
Starting NMAP check...

Starting Nmap 7.60 ( https://nmap.org ) at XXX
Nmap scan report for daq-faux-1 (X.X.X.X)
Host is up (XXX).

PORT      STATE SERVICE
10000/tcp open  snet-sensor-mgmt
MAC Address: 9A:02:57:1E:8F:01 (Unknown)

Nmap done: 1 IP address (1 host up) scanned in XXX
nmap X.X.X.X
Done.
--------------------
RESULT skip security.passwords.https Port 443 is not open on target device.

--------------------
security.passwords.telnet
--------------------
Verify all default passwords are updated and new Google provided passwords are set.
--------------------
[STARTING WITH IP:X.X.X.X, MAC:9a:02:57:1e:8f:01, PROTOCOL: telnet]
Starting NMAP check...

Starting Nmap 7.60 ( https://nmap.org ) at XXX
Nmap scan report for daq-faux-1 (X.X.X.X)
Host is up (XXX).

PORT      STATE SERVICE
10000/tcp open  snet-sensor-mgmt
MAC Address: 9A:02:57:1E:8F:01 (Unknown)

Nmap done: 1 IP address (1 host up) scanned in XXX
nmap X.X.X.X
Done.
--------------------
RESULT skip security.passwords.telnet Port 23 is not open on target device.

--------------------
security.passwords.ssh
--------------------
Verify all default passwords are updated and new Google provided passwords are set.
--------------------
[STARTING WITH IP:X.X.X.X, MAC:9a:02:57:1e:8f:01, PROTOCOL: ssh]
Starting NMAP check...

Starting Nmap 7.60 ( https://nmap.org ) at XXX
Nmap scan report for daq-faux-1 (X.X.X.X)
Host is up (XXX).

PORT      STATE SERVICE
10000/tcp open  snet-sensor-mgmt
MAC Address: 9A:02:57:1E:8F:01 (Unknown)

Nmap done: 1 IP address (1 host up) scanned in XXX
nmap X.X.X.X
Done.
--------------------
RESULT skip security.passwords.ssh Port 22 is not open on target device.

```

#### Module Config

|Attribute|Value|
|---|---|
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
manual.test.travis
--------------------

--------------------
No additional information provided
--------------------
RESULT pass manual.test.travis Manual test - for testing

```

#### Module Config

|Attribute|Value|
|---|---|
|enabled|True|

## Report complete

