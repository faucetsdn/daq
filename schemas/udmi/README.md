# UDMI Schema Target

The Universal Device Management Interface (UDMI) schema provides a high-level
specification for the management and operation of physical systems. This data is typically exchanged
with a cloud entity that can maintain a "digital twin" or "shadow device" in the cloud.
Nominally meant for use with [Googe's Cloud IoT Core](https://cloud.google.com/iot/docs/),
as a schema it can be applied to any set of data or hosting setup.

By deisgn, this schema is intended to be:
* Universal: Apply to all subsystems in a building, not a singular vertical solution.
* Device: Operations on an IoT "device," a managed entity in physical space.
* Management: Focus on device _management_, rather than command & control.
* Interface: Define an interface specification, rather than a client-library or RPC mechanism.

## Use Cases

UDMI is intended to support a few primary use-cases:
* Device Testability
* Operational Diagnostics
* Commissioning Tools
* Status and Logging Reporting
* Key Rotation, Credential Exchange
* Firmware Updates

## Design Philiosphy

* <b>Secure and Authenticated Channel:</b> Assumes a propertly secure and
authenticated channel, so those primitives are not included as part of the core specification.
* <b>Declarative Specification:</b> The schema describes the _desired_ state of the system,
relying on the underlying mechanisms to match actual state with desired state. This is
conceptually similar to Kubernetes-style configuraiton files.
* <b>Minimal Elegant Design:</b> Initially underspecified, with an eye towards making it easy to
add new capabilities in the future. <em>It is easier to add something than it is to remove it.</em>
* <b>Reduced Choices:</b> In the long run, choice leads to more work
to implement, and more ambiguity. Strive towards having only _one_ way of doing each thing.

## Validation

To verify correct operation of a real system, follow the instructions outlined in the
[validator subsystem docs](../../../docs/validator.md), which provides for a suitable
communication channel. Additional sample messages are easy to include in the regression
suite if there are new cases to test.

## Schema Structure

Schemas are broken down into several sub-schemas that address different aspects
of device management:
* State updates ([example](state.tests/example.json)) from device to cloud,
defined by [<em>state.json</em>](state.json).
* Configuration ([example](config.tests/example.json)) passed from cloud to device,
defined by [<em>config.json</em>](config.json).
* Streaming data points ([example](pointset.tests/example.json)) from device to cloud,
defined by [<em>pointset.json</em>](pointset.json).
* Logging messages ([example](logentry.tests/example.json)) from devices,
defined by [<em>logentry.json</em>](logentry.json).
* Message envelope ([example](envelope.tests/example.json)) for server-side
attributes, defined by [<em>envelope.json</em>](envelope.json).
* Device metadata ([example](metadata.tests/example.json)) stored _about_ a device,
but not directly available to the device, defined by [<em>metadata.json</em>](metadata.json).

## Message Detail Notes

### State Message

* See note below about 'State status' fields.

### Config Message

* The `report_interval_ms` field represents a periodic trigger for the device sending a `pointset`
message. If undefined then the system should only use `cov_increment` based updates instead (if defined).

### Logentry Message

* See note below about 'Logentry entries' fields.

### State status and logentry entries fields

The State and Logentry messages both have very similar `status` and `entries` sub-fields, respectively.
* State `status` entries represent 'sticky' conditions that persist until the situation is cleared,
e.g. "device disconnected".
* Logentry `entries` fields are transitory event that happen, e.g. "connection failed".
* Both `status` and `entries` fields are arrays, allowing multiple updates to be included.
* Config parse errors should be represented as a system-level device state status entry.
* The `message` field sould be a one-line representation of the triggering condition.
* The `detail` field can be multi-line and include more detail, e.g. a complete program stack-trace.
* The `category` field is a device-specific representation of which sub-system the message comes from. In
a Java environment, for example, it would be the fully qualified path name of the Class triggering the message.
* The status `timestamp` field should be the timestamp the condition was triggered, or most recently updated. It might
be different than the top-level message `timestamp` if the condition is not checked often, or is sticky until
it's cleared.
* A logentry `timestamp` field is the time that the event occured.
* The status `level` should conform to the numerical
[Stackdriver LogEntry](https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#logseverity)
levels. The `DEFAULT` value of 0 is not allowed (lowest value is 100, maximum 800).

## Design Philiophy

The design of the schema follows the following high-level guidelines.

* Follows the [API Resource Names guidline](https://cloud.google.com/apis/design/resource_names) guideline.
* Uses <em>snake_case</em> convention.
* Restricted options, to prevent fragmentation. Additional fields can easily be added
(but it's hard to take them away!).
* Structure and clarity over brevity. This is not a "compressed" format and not designed for very large structures.
