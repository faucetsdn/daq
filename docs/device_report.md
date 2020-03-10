# Device 9a:02:57:1e:8f:01, *** Make *** *** Model ***

## Test Roles

|  Role  |      Name              | Status |
|--------|------------------------|--------|
|Operator| *** Operator Name *** |        |
|Approver| *** Approver Name *** |        |

## Test Iteration

| Test             |                        |
|------------------|------------------------|
| Test report start date | 2020-02-25 13:56:13+00:00 |
| Test report end date   | 2020-02-25 14:07:48+00:00 |
| DAQ version      | 1.0.1 |
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

|Expectation|pass|fail|skip|info|gone|
|---|---|---|---|---|---|
|Required|1|1|0|0|0|
|Recommended|1|0|0|0|0|
|Other|2|3|17|1|2|

|Result|Test|Category|Expectation|Notes|
|---|---|---|---|---|
|skip|base.switch.ping|Other|Other|No local IP has been set, check ext_loip in system.conf|
|pass|base.target.ping|Connectivity|Required|target reached|
|skip|cloud.udmi.pointset|Other|Other|No device id|
|info|communication.type.broadcast|Other|Other|Broadcast packets received.|
|pass|connection.dhcp_long|Other|Other|ARP packets received.|
|fail|connection.mac_oui|Other|Other|Manufacturer prefix not found!|
|pass|connection.min_send|Other|Other|ARP packets received. Other packets received.|
|skip|connection.port_duplex|Other|Other|No local IP has been set, check ext_loip in system.conf|
|skip|connection.port_link|Other|Other|No local IP has been set, check ext_loip in system.conf|
|skip|connection.port_speed|Other|Other|No local IP has been set, check ext_loip in system.conf|
|fail|network.brute|Security|Required|Change the default password on the DUT|
|fail|network.ntp.support|Other|Other||
|skip|poe.negotiation|Other|Other|No local IP has been set, check ext_loip in system.conf|
|skip|poe.power|Other|Other|No local IP has been set, check ext_loip in system.conf|
|skip|poe.support|Other|Other|No local IP has been set, check ext_loip in system.conf|
|fail|protocol.app_min_send|Other|Other||
|skip|protocol.bacnet.pic|Other|Other|Bacnet device not found.|
|skip|protocol.bacnet.version|Other|Other|Bacnet device not found.|
|skip|security.firmware|Other|Other|Could not retrieve a firmware version with nmap. Check bacnet port.|
|skip|security.passwords.http|Other|Other|Could not lookup password info for mac-key 9a:02:57:1e:8f:01|
|skip|security.passwords.https|Other|Other|Could not lookup password info for mac-key 9a:02:57:1e:8f:01|
|skip|security.passwords.ssh|Other|Other|Could not lookup password info for mac-key 9a:02:57:1e:8f:01|
|skip|security.passwords.telnet|Other|Other|Could not lookup password info for mac-key 9a:02:57:1e:8f:01|
|pass|security.ports.nmap|Security|Recommended||
|skip|security.tls.v3|Other|Other||
|skip|security.x509|Other|Other||
|gone|unknown.fake.llama|Other|Other||
|gone|unknown.fake.monkey|Other|Other||


## Module ping

```
--------------------
Baseline ping test report
%% 57 packets captured.
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
RESULT pass base.target.ping target reached %% 10.20.43.164

```

## Module nmap

```
--------------------
security.ports.nmap
--------------------
Automatic TCP/UDP port scan using nmap
--------------------
Allowing 10000 open tcp snet-sensor-mgmt
No invalid ports found.
--------------------
RESULT pass security.ports.nmap 

```

## Module brute

```
--------------------
network.brute
--------------------
Educational test - not to be included in a production environment!
--------------------
Username:manager
Password:friend
Login success!
--------------------
RESULT fail network.brute Change the default password on the DUT

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

## Module network

```
--------------------
connection.dhcp_long
--------------------
Device sends ARP request on DHCP lease expiry.
--------------------
%% 13:56:44.587570 ARP, Request who-has 10.20.0.3 tell daq-faux-1, length 28
%% 13:56:44.587648 ARP, Reply 10.20.0.3 is-at ca:88:ca:5e:06:8b (oui Unknown), length 28
%% 13:57:13.514327 ARP, Request who-has daq-faux-1 tell 10.20.0.3, length 28
%% 13:57:13.514590 ARP, Reply daq-faux-1 is-at 9a:02:57:1e:8f:01 (oui Unknown), length 28
%% 14:00:55.982710 ARP, Request who-has daq-faux-1 tell 10.20.0.3, length 28
%% 14:00:55.982982 ARP, Request who-has 10.20.0.3 tell daq-faux-1, length 28
%% 14:00:55.983035 ARP, Reply 10.20.0.3 is-at ca:88:ca:5e:06:8b (oui Unknown), length 28
%% 14:00:55.983037 ARP, Reply daq-faux-1 is-at 9a:02:57:1e:8f:01 (oui Unknown), length 28
%% 
%% packets_count=9
RESULT pass connection.dhcp_long ARP packets received.
--------------------
connection.min_send
--------------------
Device sends data at a frequency of less than 5 minutes.
--------------------
%% 13:56:43.925908 IP 10.20.43.164.50810 > 10.20.255.255.41794: UDP, length 32
%% 13:56:44.587570 ARP, Request who-has 10.20.0.3 tell 10.20.43.164, length 28
%% 13:57:03.941786 IP 10.20.43.164.43690 > 10.20.255.255.41794: UDP, length 32
%% 13:57:08.267933 IP 10.20.43.164.68 > 10.20.0.3.67: BOOTP/DHCP, Request from 9a:02:57:1e:8f:01, length 300
%% 13:57:13.514590 ARP, Reply 10.20.43.164 is-at 9a:02:57:1e:8f:01, length 28
%% 13:57:23.961823 IP 10.20.43.164.41983 > 10.20.255.255.41794: UDP, length 32
%% 13:57:43.982894 IP 10.20.43.164.43358 > 10.20.255.255.41794: UDP, length 32
%% 13:58:04.003633 IP 10.20.43.164.58288 > 10.20.255.255.41794: UDP, length 32
%% 13:58:24.024931 IP 10.20.43.164.60332 > 10.20.255.255.41794: UDP, length 32
%% packets_count=9
RESULT pass connection.min_send ARP packets received. Other packets received.
--------------------
communication.type.broadcast
--------------------
Device sends unicast or broadcast packets.
--------------------
RESULT info communication.type.broadcast Broadcast packets received.
--------------------
protocol.app_min_send
--------------------
Device sends application packets at a frequency of less than 5 minutes.
--------------------
RESULT fail protocol.app_min_send 
--------------------
network.ntp.support
--------------------
Device sends NTP request packets.
--------------------
RESULT fail network.ntp.support 
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
Collecting TLS cert from target address %% 10.20.43.164
IOException unable to connect to server.

--------------------
security.tls.v3
--------------------
Verify the device supports TLS 1.2 or above (as a client)
--------------------
See log above
--------------------
RESULT skip security.tls.v3

--------------------
security.x509
--------------------
Verify the devices supports RFC 2459 - Internet X.509 Public Key Infrastructure Certificate and CRL Profile
--------------------
See log above
--------------------
RESULT skip security.x509

```

## Module password

```
--------------------
security.passwords.http
--------------------
Verify all default password have been updated. Ensure new Google provided passwords are set
--------------------
Redacted Log
--------------------
RESULT skip security.passwords.http Could not lookup password info for mac-key 9a:02:57:1e:8f:01

--------------------
security.passwords.https
--------------------
Verify all default password have been updated. Ensure new Google provided passwords are set
--------------------
Redacted Log
--------------------
RESULT skip security.passwords.https Could not lookup password info for mac-key 9a:02:57:1e:8f:01

--------------------
security.passwords.telnet
--------------------
Verify all default password have been updated. Ensure new Google provided passwords are set
--------------------
Redacted Log
--------------------
RESULT skip security.passwords.telnet Could not lookup password info for mac-key 9a:02:57:1e:8f:01

--------------------
security.passwords.ssh
--------------------
Verify all default password have been updated. Ensure new Google provided passwords are set
--------------------
Redacted Log
--------------------
RESULT skip security.passwords.ssh Could not lookup password info for mac-key 9a:02:57:1e:8f:01

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

