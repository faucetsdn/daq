# Device Gateway

The _gateway_ functionality is used for systems that have legacy, heritage,
or traditional devices that do not communicate directly to the cloud using
UDMI. For example, an older BacNET based system could use a gateway to
translate on-prem communications into UDMI.

See the
(Google Clout IoT Core Gateway Documentation)[https://cloud.google.com/iot/docs/how-tos/gateways]
for an overview of how gateways work. This document details specifically how
this manifests itself using UDMI. Conceptually, there are two types of
entities involved: the _gateway device_, and the _proxied device_. Both of
these are 'devices' in the sense that they have an entry in a cloud registry
and have device-level UDMI data, but they have fundamentally different roles.

The process of _discovery_, which is where something discovers other devices
on the local network, is conceptually related but functionally distinct and
separate than a gateway.

## Gateway Operation

The general sequence of events for gateway operation is:
1. Optional metadata specifies configuration paramaters that should be used
at install time to properly (manually) setup the device.
2. On startup, the gateway connects to the cloud and receives a configuration
block that details which _proxy devices_ the gateway should proxy for.
3. logentry events are used to indicate general progress and activity from
the gateway.
4. Gateway 'attaches' (Cloud IoT terminology) to the proxied devices,
receiving a configuration block for each proxied device.
5. Any attch errors are indicated in the gateway status block.
6. The proxy device configuration block specifies any local connection
parameters for the proxied device, e.g. the BacNET device id.
7. The gateway proxies communication to/from the device, translating between
native (e.g. BacNET) communications and UDMI-based messages.

### config

The gateway config block simply specifies the list of target proxy devices.
On a config update, the gateway is responsible for handling any change in
this list (added or removed devices). The details of proxied devices are
kept to a minimum here (IDs only) to avoid overflowing the allowed block
size in cases where there are a large number of devices.

### state

Any attach errors, e.g. the gateway can not successfully attach to the target
device, should be reported here, and a logentry message used to detail the
nature of the problem. If the gateway can attach successfully, any other
errors, e.g. the inability to communicate with the device over the local
network, should be indicated as part of the proxy device status block.

### logentry

Telemety from the gateway would primarily consist of logentry messages, which
provide a running comentary about gateway operation. Specificaly, if there
is an error attaching, then there should be appropriate logging to help
diagnose the problem.

### metadata

The gateway metadata block specifies any information necessary either for the
initial (manual) configuration of the device or ongoing validation of
operation. E.g., if a gateway device has a unique MAC address used for
local communications, it would be indicated here.

## Proxy Device Operation

### config
### state
### telemetry
### metadata
