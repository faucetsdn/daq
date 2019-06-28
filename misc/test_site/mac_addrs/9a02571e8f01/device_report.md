# Device 9a02571e8f01, 2019-06-28 14:53:00+00:00 to 2019-06-28 14:55:16+00:00

|  Role  |      Name              | Status |
|--------|------------------------|--------|
|Operator| *** Operator Name *** |        |
|Approver| *** Approver Name *** |        |

| Test iteration   |                        |
|------------------|------------------------|
| Test report date | 2019-06-28T14:52:59.494Z |
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

|Result|Test|Notes|
|---|---|---|
|skip|base.switch.ping|other||
|pass|base.target.ping|required|target|
|skip|cloud.udmi.pointset|other|No device id.|
|fail|connection.mac_oui|other||
|fail|network.brute|required||
|fail|protocol.bacnet.version|other||
|pass|security.ports.nmap|recommended||
|skip|security.tls.v3|other||
|skip|security.x509|other||

## Module ping

```
Baseline ping test report
%% 31 packets captured.
RESULT skip base.switch.ping
RESULT pass base.target.ping target %% 10.20.3.164
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

