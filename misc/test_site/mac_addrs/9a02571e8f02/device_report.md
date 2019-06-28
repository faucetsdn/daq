# Device 9a02571e8f02, 2019-06-28 16:28:30+00:00 to 2019-06-28 16:33:57+00:00

|  Role  |      Name              | Status |
|--------|------------------------|--------|
|Operator| *** Operator Name *** |        |
|Approver| *** Approver Name *** |        |

| Test iteration   |                        |
|------------------|------------------------|
| Test report date | 2019-06-28T16:28:29.964Z |
| DAQ version      | 1.0.0 |
| Attempt number   |  |

## Device Identification

| Device            | Entry              |
|-------------------|--------------------|
| Name              | *** Name *** |
| GUID              | *** GUID *** |
| MAC addr          | 9a:02:57:1e:8f:02 |
| Hostname          | *** Network Hostname *** |
| Type              | *** Type *** |
| Make              | *** Make *** |
| Model             | *** Model *** |
| Serial Number     | *** Serial *** |
| Firmware Version  |  |

## Device Description

![Image of device]()




### Device documentation

[Device datasheets]()
[Device manuals]()

## Report summary

|Expected|pass|fail|skip|
|---|---|---|---|
|Required|2|0|0|
|recommended|0|0|0|
|other|1|4|1|
|Recommended|0|1|0|

|Result|Test|Expected|Notes|
|---|---|---|---|
|skip|base.switch.ping|other||
|pass|base.target.ping|Required|target|
|pass|cloud.udmi.pointset|other||
|fail|connection.mac_oui|other||
|pass|network.brute|Required||
|fail|protocol.bacnet.version|other||
|fail|security.ports.nmap|Recommended||
|fail|security.tls.v3|other||
|fail|security.x509|other||


## Module ping

```
Baseline ping test report
%% 463 packets captured.
RESULT skip base.switch.ping
RESULT pass base.target.ping target %% 10.20.36.165
```

## Module nmap

```
Failing 443 open tcp https ,
Failing 10000 open tcp snet-sensor-mgmt
RESULT fail security.ports.nmap
```

## Module brute

```
Connection closed by foreign host.
Failed after retries.
RESULT pass network.brute
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
Cipher:
TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
Certificate is expired.
RESULT fail security.tls.v3
RESULT fail security.x509
```

## Module udmi

```
RESULT pass cloud.udmi.pointset
```

## Report complete

