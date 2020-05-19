# Device Remediation Test

## Device {{ run_info.mac_addr }}

# {{ device_info.make }} {{ device_info.model }}

## Test Iteration

Test                   |
---------------------- | ----------------------------
Test report start date | {{ start_time }}
Test report end date   | {{ end_time}}
DAQ version            | {{ run_info.daq_version }}

## Device Identification

Device           | Entry
---------------- | ----------------------------------
Name             | {{ device_info.name }}
GUID             | {{ device_info.guid }}
MAC address      | {{ run_info.mac_addr }}
Hostname         | {{ device_info.hostname }}
Type             | {{ device_info.type }}
Make             | {{ device_info.make }}
Model            | {{ device_info.model }}
Serial Number    | {{ device_info.serial }}
Firmware Version | {{ device_info.firmware_version }}
