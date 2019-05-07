|  Role  |      Name              |
|--------|------------------------|
|Operator| {{ process.operator }} |
|Reviewer| {{ process.reviewer }} |
|Approver| {{ process.approver }} |
|--------|------------------------|
| Test report date | {{ run_info.started }} |
| DAQ version      | {{ run_info.daq_version }} |

## Device Identification

| Device        | Entry              |
|---------------|--------------------|
| Name          | {{ device_info.name }} |
| GUID          | {{ device_info.guid }} |
| MAC addr      | {{ run_info.mac_addr }} |
| Hostname      | {{ device_info.hostname }} |
| Type          | {{ device_info.type }} |
| Make          | {{ device_info.make }} |
| Model         | {{ device_info.model }} |
| Serial Number | {{ device_info.serial }} |
| Version       | {{ device_info.version }} |

## Device Description

{{ device_description }}
