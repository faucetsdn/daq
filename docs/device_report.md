# Device 9a02571e8f01, 2019-06-28 22:40:21+00:00 to 2019-06-28 22:42:10+00:00

|  Role  |      Name              | Status |
|--------|------------------------|--------|
|Operator| *** Operator Name *** |        |
|Approver| *** Approver Name *** |        |

| Test iteration   |                        |
|------------------|------------------------|
| Test report date | 2019-06-28T22:40:20.660Z |
| DAQ version      | 1.0.0 |
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

|Category|Result|
|---|---|
|Security|PASS|
|Other|1/2|
|Connectivity|n/a|

|Expected|pass|fail|skip|gone|
|---|---|---|---|---|
|Required|1|1|0|0|
|Recommended|1|0|0|0|
|Other|0|2|4|2|

|Result|Test|Expected|Notes|
|---|---|---|---|
|skip|base.switch.ping|Other||
|pass|base.target.ping|Required|target|
|skip|cloud.udmi.pointset|Other|No device id.|
|fail|connection.mac_oui|Other||
|fail|network.brute|Required||
|fail|protocol.bacnet.version|Other||
|pass|security.ports.nmap|Recommended||
|skip|security.tls.v3|Other||
|skip|security.x509|Other||
|gone|unknown.fake.llama|Other||
|gone|unknown.fake.monkey|Other||


## Module ping

```
Baseline ping test report
%% 39 packets captured.
RESULT skip base.switch.ping
RESULT pass base.target.ping target %% 10.20.71.164
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

