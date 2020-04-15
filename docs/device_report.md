# Device 9a:02:57:1e:8f:01, *** Make *** *** Model ***

## Test Roles

|  Role  |      Name              | Status |
|--------|------------------------|--------|
|Operator| *** Operator Name *** |        |
|Approver| *** Approver Name *** |        |

## Test Iteration

| Test             |                        |
|------------------|------------------------|
| Test report start date | 2020-04-15 02:17:03+00:00 |
| Test report end date   | 2020-04-15 02:20:12+00:00 |
| DAQ version      |  |
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
|Security|0/1|
|Other|1/2|
|Connectivity|n/a|

|Expectation|pass|fail|skip|gone|
|---|---|---|---|---|
|Required|1|0|0|0|
|Recommended|0|1|0|0|
|Other|0|4|18|2|

|Result|Test|Category|Expectation|Notes|
|---|---|---|---|---|
|skip|base.switch.ping|Other|Other|No local IP has been set, check ext_loip in system.conf|
|pass|base.target.ping|Connectivity|Required|target reached|
|skip|cloud.udmi.pointset|Other|Other|No device id|
|fail|connection.mac_oui|Other|Other|Manufacturer prefix not found!|
|skip|connection.port_duplex|Other|Other|No local IP has been set, check ext_loip in system.conf|
|skip|connection.port_link|Other|Other|No local IP has been set, check ext_loip in system.conf|
|skip|connection.port_speed|Other|Other|No local IP has been set, check ext_loip in system.conf|
|skip|poe.negotiation|Other|Other|No local IP has been set, check ext_loip in system.conf|
|skip|poe.power|Other|Other|No local IP has been set, check ext_loip in system.conf|
|skip|poe.support|Other|Other|No local IP has been set, check ext_loip in system.conf|
|skip|protocol.bacnet.pic|Other|Other|Bacnet device not found.|
|skip|protocol.bacnet.version|Other|Other|Bacnet device not found.|
|skip|security.firmware|Other|Other|Could not retrieve a firmware version with nmap. Check bacnet port.|
|skip|security.passwords.http|Other|Other|Port 80 is not open on target device.|
|skip|security.passwords.https|Other|Other|Port 443 is not open on target device.|
|skip|security.passwords.ssh|Other|Other|Port 22 is not open on target device.|
|skip|security.passwords.telnet|Other|Other|Port 23 is not open on target device.|
|fail|security.ports.nmap|Security|Recommended|Some disallowed ports are open: 47808|
|skip|security.tls.v1|Other|Other||
|fail|security.tls.v1.x509|Other|Other||
|skip|security.tls.v1_2|Other|Other||
|fail|security.tls.v1_2.x509|Other|Other||
|skip|security.tls.v1_3|Other|Other||
|fail|security.tls.v1_3.x509|Other|Other||
|gone|unknown.fake.llama|Other|Other||
|gone|unknown.fake.monkey|Other|Other||


## Module ping

```
--------------------
Baseline ping test report
%% 34 packets captured.
LOCAL_IP not configured, assuming no network switch

Done with basic connectivity tests

--------------------
base.switch.ping
--------------------
Attempt to ping the OpenFlow compatible switch configured in system.conf
--------------------
See log above
--------------------
RESULT skip base.switch.ping No local IP has been set, check ext_loip in system.conf

--------------------
base.target.ping
--------------------
Attempt to ping the Device Under Test
--------------------
See log above
--------------------
RESULT pass base.target.ping target reached %% 10.20.87.164

```

## Module nmap

```
--------------------
security.ports.nmap
--------------------
Automatic TCP/UDP port scan using nmap
--------------------
# Nmap 7.60 scan initiated Wed Apr 15 02:18:57 2020 as: nmap -v -n -T5 -sT -sU --host-timeout=4m --open -pU:47808,T:23,443,80, -oG /tmp/nmap.log 10.20.87.164
# Ports scanned: TCP(3;23,80,443) UDP(1;47808) SCTP(0;) PROTOCOLS(0;)
Host: 10.20.87.164 ()	Status: Up
Host: 10.20.87.164 ()	Ports: 47808/open|filtered/udp//bacnet///	Ignored State: closed (3)
# Nmap done at Wed Apr 15 02:18:58 2020 -- 1 IP address (1 host up) scanned in 0.54 seconds
Failing 47808 open|filtered udp bacnet
--------------------
RESULT fail security.ports.nmap Some disallowed ports are open: 47808

```

## Module discover

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

## Module switch

```
--------------------
connection.port_link
--------------------
Connect the device to the network switch. Check the device and the switch for the green connection light & no errors
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip connection.port_link No local IP has been set, check ext_loip in system.conf

--------------------
connection.port_speed
--------------------
Verify the device auto-negotiates connection speed
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip connection.port_speed No local IP has been set, check ext_loip in system.conf

--------------------
connection.port_duplex
--------------------
Verify the device supports full duplex
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip connection.port_duplex No local IP has been set, check ext_loip in system.conf

--------------------
poe.power
--------------------
Verify that the device draws less than the maximum power allocated by the port. This is 15.4W for 802.3af and 30W for 802.3at
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip poe.power No local IP has been set, check ext_loip in system.conf

--------------------
poe.negotiation
--------------------
Verify the device autonegotiates power requirements
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip poe.negotiation No local IP has been set, check ext_loip in system.conf

--------------------
poe.support
--------------------
Verify if the device supports PoE
--------------------
LOCAL_IP not configured, assuming no network switch.
--------------------
RESULT skip poe.support No local IP has been set, check ext_loip in system.conf

```

## Module macoui

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

## Module bacext

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
 Bacnet device not found... Pics check cannot be performed.
--------------------
RESULT skip protocol.bacnet.pic Bacnet device not found.

```

## Module tls

```
--------------------
Collecting TLS cert from target address %% 10.20.87.164

--------------------
security.tls.v1
--------------------
Verify the device supports TLS 1.0 (as a client)
--------------------
See log above
--------------------
RESULT skip security.tls.v1

--------------------
security.tls.v1.x509
--------------------
Verify the devices supports RFC 2459 - Internet X.509 Public Key Infrastructure Certificate and CRL Profile
--------------------
See log above
--------------------
RESULT fail security.tls.v1.x509

--------------------
security.tls.v1_2
--------------------
Verify the device supports TLS 1.2 (as a client)
--------------------
See log above
--------------------
RESULT skip security.tls.v1_2

--------------------
security.tls.v1_2.x509
--------------------
null
--------------------
See log above
--------------------
RESULT fail security.tls.v1_2.x509

--------------------
security.tls.v1_3
--------------------
Verify the device supports TLS 1.3 (as a client)
--------------------
See log above
--------------------
RESULT skip security.tls.v1_3

--------------------
security.tls.v1_3.x509
--------------------
Verify the devices supports RFC 2459 - Internet X.509 Public Key Infrastructure Certificate and CRL Profile
--------------------
See log above
--------------------
RESULT fail security.tls.v1_3.x509

```

## Module password

```
--------------------
security.passwords.http
--------------------
Verify all default passwords are updated and new Google provided passwords are set.
--------------------
%% [STARTING WITH IP:10.20.87.164, MAC:9a:02:57:1e:8f:01, PROTOCOL: http]
%% Starting NMAP check...
%% 
%% Starting Nmap 7.60 ( https://nmap.org ) at 2020-04-15 02:19 UTC
%% Nmap scan report for daq-faux-1 (10.20.87.164)
%% Host is up (0.000043s latency).
%% Not shown: 999 closed ports
%% PORT      STATE SERVICE
%% 10000/tcp open  snet-sensor-mgmt
%% MAC Address: 9A:02:57:1E:8F:01 (Unknown)
%% 
%% Nmap done: 1 IP address (1 host up) scanned in 1.68 seconds
%% nmap 10.20.87.164
%% Done.
--------------------
RESULT skip security.passwords.http Port 80 is not open on target device.

--------------------
security.passwords.https
--------------------
Verify all default passwords are updated and new Google provided passwords are set.
--------------------
%% [STARTING WITH IP:10.20.87.164, MAC:9a:02:57:1e:8f:01, PROTOCOL: https]
%% Starting NMAP check...
%% 
%% Starting Nmap 7.60 ( https://nmap.org ) at 2020-04-15 02:19 UTC
%% Nmap scan report for daq-faux-1 (10.20.87.164)
%% Host is up (0.00013s latency).
%% Not shown: 999 closed ports
%% PORT      STATE SERVICE
%% 10000/tcp open  snet-sensor-mgmt
%% MAC Address: 9A:02:57:1E:8F:01 (Unknown)
%% 
%% Nmap done: 1 IP address (1 host up) scanned in 1.91 seconds
%% nmap 10.20.87.164
%% Done.
--------------------
RESULT skip security.passwords.https Port 443 is not open on target device.

--------------------
security.passwords.telnet
--------------------
Verify all default passwords are updated and new Google provided passwords are set.
--------------------
%% [STARTING WITH IP:10.20.87.164, MAC:9a:02:57:1e:8f:01, PROTOCOL: telnet]
%% Starting NMAP check...
%% 
%% Starting Nmap 7.60 ( https://nmap.org ) at 2020-04-15 02:19 UTC
%% Nmap scan report for daq-faux-1 (10.20.87.164)
%% Host is up (0.000081s latency).
%% Not shown: 999 closed ports
%% PORT      STATE SERVICE
%% 10000/tcp open  snet-sensor-mgmt
%% MAC Address: 9A:02:57:1E:8F:01 (Unknown)
%% 
%% Nmap done: 1 IP address (1 host up) scanned in 1.90 seconds
%% nmap 10.20.87.164
%% Done.
--------------------
RESULT skip security.passwords.telnet Port 23 is not open on target device.

--------------------
security.passwords.ssh
--------------------
Verify all default passwords are updated and new Google provided passwords are set.
--------------------
%% [STARTING WITH IP:10.20.87.164, MAC:9a:02:57:1e:8f:01, PROTOCOL: ssh]
%% Starting NMAP check...
%% 
%% Starting Nmap 7.60 ( https://nmap.org ) at 2020-04-15 02:19 UTC
%% Nmap scan report for daq-faux-1 (10.20.87.164)
%% Host is up (0.000076s latency).
%% Not shown: 999 closed ports
%% PORT      STATE SERVICE
%% 10000/tcp open  snet-sensor-mgmt
%% MAC Address: 9A:02:57:1E:8F:01 (Unknown)
%% 
%% Nmap done: 1 IP address (1 host up) scanned in 1.91 seconds
%% nmap 10.20.87.164
%% Done.
--------------------
RESULT skip security.passwords.ssh Port 22 is not open on target device.

```

## Module udmi

```
--------------------
cloud.udmi.pointset
--------------------
Validates device payload against the UDMI schema
--------------------
Device id is null, skipping.
--------------------
RESULT skip cloud.udmi.pointset No device id

```

## Report complete

