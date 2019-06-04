|  Role  |      Name              | Status |
|--------|------------------------|--------|
|Operator| {{ process.operator }} |        |
|Approver| {{ process.approver }} |        |

| Test iteration   |                        |
|------------------|------------------------|
| Test report date | {{ run_info.started }} |
| DAQ version      | {{ run_info.daq_version }} |
| Attempt number   | {{ process.attempt_number }} |

## Device Identification

| Device            | Entry              |
|-------------------|--------------------|
| Name              | {{ device_info.name }} |
| GUID              | {{ device_info.guid }} |
| MAC addr          | {{ run_info.mac_addr }} |
| Hostname          | {{ device_info.hostname }} |
| Type              | {{ device_info.type }} |
| Make              | {{ device_info.make }} |
| Model             | {{ device_info.model }} |
| Serial Number     | {{ device_info.serial }} |
| Firmware Version  | {{ device_info.firmware_version }} |

## Device Description

![Image of device]({{ device_image }})

{{ device_description }}


### Device documentation

[Device datasheets]({{ device_datasheets_url }})
[Device manuals]({{ device_manuals_url }})
