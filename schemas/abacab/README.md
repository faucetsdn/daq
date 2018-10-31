# ABACAB Schema Target

The [ABACAB](https://www.youtube.com/watch?v=QbjfesCI254) Schema is a simple
formatting meant to collect data from physical systems such that it can be collected and
organized in a database, ultimately being able to represent a device with a "digital twin"
or "shadow device" in the cloud. Nominally meant for use with
[Googe's Cloud IoT Core](https://cloud.google.com/iot/docs/), as a schema it can be
applied to any set of data.

To verify correct operation of a real system, follow the instructions outlined in the
[validator subsystem docs](../../../docs/validator.md). Additional sample messages are
easy to include in the regression suite if there is something platform-specific that needs
to be tested.

## Schema Structure

Schemas are broken down into several sub-schemas that address different message types:
* [<em>state</em>](state.json):
Sporadic state updates from device to cloud ([example](state.tests/example.json)).
* [<em>config</em>](config.json):
Configuration passed from cloud to device ([example](config.tests/example.json)).
* [<em>pointset</em>](pointset.json):
Streaming data points from device to cloud ([example](pointset.tests/example.json)).
* [<em>logentry</em>](logentry.json):
Logging messages from devices ([example](logentry.tests/example.json)).
* [<em>envelope</em>](envelope.json):
The message envelope that is automatically generated for messages during cloud-side processing ([example](envelope.tests/example.json)).
* [<em>metadata</em>](metadata.json):
Device metadata stored in the cloud _about_ a device, but not generally available to the device ([example](metadata.tests/example.json)).

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
