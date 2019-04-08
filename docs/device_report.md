# DAQ scan report for device 9a02571e8f01
Started %% 2019-04-08 16:45:36+00:00

|  Role  |      Name       |
|--------|-----------------|
|Operator| <operator_name> |
|Reviewer| <reviewer_name> |
|Approver| <approver_name> |
|--------|-----------------|
|Test report date    | <test_timestamp>  |
|Test report revision| <revision_number> |

## Device identification

| Device        | Entry              |
|---------------|--------------------|
| Name          | <device_name>      |
| GUID          | <device_guid>      |
| MAC addr      | <mac_address>      |
| Hostname      | <hostname>         |
| Type          | <device_type>      |
| Manufacturer  | <manufacturer>     |
| Model         | <model>            |
| Serial Number | <serial_number>    |
| Version       | <firmware_version> |

## Device description

Free text including description of device and links to more information
(datasheets, manuals, installation notes, etc.)

## Test priorities

| Test Name       | Priority    |
|-----------------|-------------|
| category1.test1 | REQUIRED    |
| category1.test2 | RECOMMENDED |
| category2.test1 | REQUIRED    |

## Report summary

skip base.switch.ping
pass base.target.ping target %% 10.20.10.38
fail security.ports.nmap

## Module ping

```
Baseline ping test report
%% 38 packets captured.
RESULT skip base.switch.ping
RESULT pass base.target.ping target %% 10.20.10.38
```

## Module nmap

```
10000/open/tcp//snet-sensor-mgmt///
RESULT fail security.ports.nmap
```

## Module brute

```
Username:manager
Password:friend
Login success!
```

## Module switch

```
LOCAL_IP not configured, assuming no network switch.
```

## Report complete

