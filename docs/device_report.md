# DAQ scan report for device 9a02571e8f01
Started 2019-03-23 14:47:25+00:00

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

```
skip base.switch.ping
pass base.target.ping target
pass security.ports.nmap
```

## Module ping

```
Baseline ping test report
# 98 packets captured.
RESULT skip base.switch.ping
RESULT pass base.target.ping target # 10.20.32.38
```

## Module nmap

```
No open ports found.
RESULT pass security.ports.nmap
```

## Module brute

```
Target port 10000 not open.
```

## Module switch

```
LOCAL_IP not configured, assuming no network switch.
```

## Report complete

