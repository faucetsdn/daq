# Device 9a:02:57:1e:8f:01, *** Make *** *** Model ***

## Test Roles

|  Role  |      Name              | Status |
|--------|------------------------|--------|
|Operator| *** Operator Name *** |        |
|Approver| *** Approver Name *** |        |

## Test Iteration

| Test             |                        |
|------------------|------------------------|
| Test report start date | 2019-06-29 21:30:06+00:00 |
| Test report end date   | 2019-06-29 21:37:30+00:00 |
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
|Other|0|2|4|2|

|Result|Test|Category|Expectation|Notes|
|---|---|---|---|---|
|skip|base.switch.ping|Other|Other||
|pass|base.target.ping|Connectivity|Required|target|
|skip|cloud.udmi.pointset|Other|Other|No device id.|
|fail|connection.mac_oui|Other|Other||
|fail|network.brute|Security|Required||
|fail|protocol.bacnet.version|Other|Other||
|pass|security.ports.nmap|Security|Recommended||
|skip|security.tls.v3|Other|Other||
|skip|security.x509|Other|Other||
|gone|unknown.fake.llama|Other|Other||
|gone|unknown.fake.monkey|Other|Other||


## Module ping

```
Baseline ping test report
%% 107 packets captured.
RESULT skip base.switch.ping
RESULT pass base.target.ping target %% 10.20.96.164
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

## Module switch

```
LOCAL_IP not configured, assuming no network switch.
```

## Module macoui

```
Mac OUI Test
RESULT fail connection.mac_oui
```

## Module bacext

```
RESULT fail protocol.bacnet.version
```

## Module tls

```
IOException unable to connect to server.
RESULT skip security.tls.v3
RESULT skip security.x509
```

## Module udmi

```
RESULT skip cloud.udmi.pointset No device id.
```

## Report complete

