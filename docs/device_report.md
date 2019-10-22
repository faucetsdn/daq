# Device 9a:02:57:1e:8f:01, *** Make *** *** Model ***

## Test Roles

|  Role  |      Name              | Status |
|--------|------------------------|--------|
|Operator| *** Operator Name *** |        |
|Approver| *** Approver Name *** |        |

## Test Iteration

| Test             |                        |
|------------------|------------------------|
| Test report start date | 2019-10-22 09:34:33+00:00 |
| Test report end date   | 2019-10-22 09:41:18+00:00 |
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

|Expectation|pass|fail|skip|gone|
|---|---|---|---|---|
|Required|1|1|0|0|
|Recommended|1|0|0|0|
|Other|0|1|17|2|

|Result|Test|Category|Expectation|Notes|
|---|---|---|---|---|
|skip|base.switch.ping|Other|Other||
|pass|base.target.ping|Connectivity|Required|target|
|skip|cloud.udmi.pointset|Other|Other|No device id.|
|fail|connection.mac_oui|Other|Other||
|skip|connection.port_duplex|Other|Other||
|skip|connection.port_link|Other|Other||
|skip|connection.port_speed|Other|Other||
|fail|network.brute|Security|Required||
|skip|poe.negotiation|Other|Other||
|skip|poe.power|Other|Other||
|skip|poe.support|Other|Other||
|skip|protocol.bacnet.pic|Other|Other|Bacnet device not found... Pics check cannot be performed.|
|skip|protocol.bacnet.version|Other|Other|Bacnet device not found.|
|skip|security.firmware|Other|Other|Could not retrieve a firmware version with nmap.|
|skip|security.passwords.http|Other|Other|Device does not have a valid mac address|
|skip|security.passwords.https|Other|Other|Device does not have a valid mac address|
|skip|security.passwords.ssh|Other|Other|Device does not have a valid mac address|
|skip|security.passwords.telnet|Other|Other|Device does not have a valid mac address|
|pass|security.ports.nmap|Security|Recommended||
|skip|security.tls.v3|Other|Other||
|skip|security.x509|Other|Other||
|gone|unknown.fake.llama|Other|Other||
|gone|unknown.fake.monkey|Other|Other||


## Module ping

```
Baseline ping test report
%% 64 packets captured.
RESULT skip base.switch.ping
RESULT pass base.target.ping target %% 10.20.34.164
```

## Module nmap

```
Allowing 10000 open tcp snet-sensor-mgmt
No invalid ports found.
RESULT pass security.ports.nmap
```

## Module brute

```
Username:manager
Password:friend
Login success!
RESULT fail network.brute
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
Firmware test complete
--------------------
RESULT skip security.firmware Could not retrieve a firmware version with nmap.
```

## Module switch

```
LOCAL_IP not configured, assuming no network switch.
RESULT skip connection.port_link
RESULT skip connection.port_speed
RESULT skip connection.port_duplex
RESULT skip poe.power
RESULT skip poe.negotiation
RESULT skip poe.support
```

## Module macoui

```
Mac OUI Test
RESULT fail connection.mac_oui
```

## Module bacext

```
RESULT skip protocol.bacnet.version Bacnet device not found.
RESULT skip protocol.bacnet.pic Bacnet device not found... Pics check cannot be performed.
```

## Module tls

```
IOException unable to connect to server.
RESULT skip security.tls.v3
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
RESULT skip security.passwords.http Device does not have a valid mac address

--------------------
security.passwords.https
--------------------
Verify all default password have been updated. Ensure new Google provided passwords are set
--------------------
Redacted Log
--------------------
RESULT skip security.passwords.https Device does not have a valid mac address

--------------------
security.passwords.telnet
--------------------
Verify all default password have been updated. Ensure new Google provided passwords are set
--------------------
Redacted Log
--------------------
RESULT skip security.passwords.telnet Device does not have a valid mac address

--------------------
security.passwords.ssh
--------------------
Verify all default password have been updated. Ensure new Google provided passwords are set
--------------------
Redacted Log
--------------------
RESULT skip security.passwords.ssh Device does not have a valid mac address

```

## Module udmi

```
RESULT skip cloud.udmi.pointset No device id.
```

## Report complete

