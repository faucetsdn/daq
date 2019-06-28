# PubSub Setup Documentation

This document describes the [GCP PubSub in Cloud IoT](https://cloud.google.com/iot-core/) mechanism for
processing device messages. There are three major message types employed by the system:
* <b>Config</b>: Messages sent from cloud-to-device that _configure_ the device (idempotent).
* <b>State</b>: Messags sent from device-to-cloud reporting _state_ form the device (idempotent).
* <b>Events</b>: Messages sent from device-to-cloud for streaming _events_ (non-idempotent).

The exact semantic meaning of theses is determined by the underlying schema used. E.g., the
[UDMI Schema](../schemas/udmi/README.md) specifies one set of conventions for managing IoT devices.

## Validator Configuration

Streaming validation validates a stream of messages pulled from a GCP PubSub topic. There are three values
in the `local/system.conf` file required to make it work:
* `gcp_cred`: The service account credentials, as per the general [DAQ Firebase setup](firebase.md).
* `gcp_topic`: The _PubSub_ (not MQTT) topic name.
* `schema_path`: Indicates which schema to validate against.

You will need to add full Project Editor permissions for the service account.
E.g., to validate messages against the UDMI schema on the `projects/gcp-account/topics/target` topic,
there should be something like:

<pre>
~/daq$ <b>fgrep gcp_ local/system.conf</b>
gcp_cred=local/gcp-account-de56aa4b1e47.json
gcp_topic=target
schema_path=schemas/udmi
</pre>

## Message/Schema Mapping

When using the
[GCP Cloud IoT Core MQTT Bridge](https://cloud.google.com/iot/docs/how-tos/mqtt-bridge#publishing_telemetry_events)
there are multiple ways the subschema used during validation is chosen.
* An `events` message is validated against the sub-schema indicated by the MQTT topic `subFolder`. E.g., the MQTT
topic `/devices/{device-id}/events/pointset` will be validated against `.../pointset.json`.
* [Device state messages](https://cloud.google.com/iot/docs/how-tos/config/getting-state#reporting_device_state)
are validated against the `.../state.json` schema.
* All messages have their attributes validated against the `.../attributes.json` schema. These attributes are
automatically defined by the MQTT Client ID and Topic, so are not explicitly included in any message payload.
* The `config` messages are artifically injected into the `target` PubSub topic by the configuration script
(below) so they can be easily checked by the validation engine.

The simple `state_shunt` function in `daq/functions/state_shunt` will automatically send state update messages
to the `target` PubSub topic. Install this function to enable validation of state updates. (Also make sure to
configure the Cloud IoT project to send state message to the state topic!)

## Pubber Reference Client

The [Pubber Reference Client](pubber.md) is a complete reference client that can be used to test out streaming
validation in absence of a real known-working device. The basic setup and documentation listed on the Pubber
page are assumed to be "running in the background" for the other examples in this section.

## Streaming Validation

Running the `bin/validate` script will will parse the configuration file and automatically start
verifying PubSub messages against the indicated schema. Using the `pubber` client, the output
should look something like:
<pre>
~/daq$ <b>bin/validate</b>
Loading config from local/system.conf

BUILD SUCCESSFUL in 3s
2 actionable tasks: 2 executed
Using credentials from /home/user/daq/local/gcp-account-de56aa4b1e47.json
Executing validator /home/user/daq/schemas/udmi pubsub:target...
Running schema . in /home/user/daq/schemas/udmi
Ignoring subfolders []
Results will be uploaded to https://console.cloud.google.com/firestore/data/registries/?project=gcp-account
Also found in such directories as /home/user/daq/schemas/udmi/out
Connecting to pubsub topic target
Entering pubsub message loop on projects/gcp-account/subscriptions/daq-validator
Success validating out/state_GAT-001.json
Success validating out/state_GAT-001.json
Success validating out/state_GAT-001.json
Success validating out/pointset_GAT-001.json
Success validating out/state_GAT-001.json
Success validating out/pointset_GAT-001.json
Success validating out/pointset_GAT-001.json
&hellip;
</pre>

If there are no _state_ validation messages (but there are _pointset_ ones), then the `state_shunt`
function described above is not installed properly.

## Injecting Configuration

The `validator/bin/config` script can be used to inject a configuration message to a device:
<pre>
~/daq$ <b>validator/bin/config GAT-001 schemas/udmi/config.tests/gateway.json</b>
Configuring gcp-account:us-central1:sensor_hub:GAT-001 from schemas/udmi/config.tests/gateway.json
messageIds:
- '301010492284043'
Updated configuration for device [GAT-001].
</pre>

If using the `pubber` client, there should be a corresponding flury of activity:
<pre>
&hellip;
[pool-1-thread-1] INFO daq.pubber.Pubber - Sending test message for sensor_hub/GAT-001
[pool-1-thread-1] INFO daq.pubber.Pubber - Sending test message for sensor_hub/GAT-001
[MQTT Call: projects/gcp-account/locations/us-central1/registries/sensor_hub/devices/GAT-001] INFO daq.pubber.Pubber - Received new config daq.udmi.Message$Config@3666b3a5
[MQTT Call: projects/gcp-account/locations/us-central1/registries/sensor_hub/devices/GAT-001] INFO daq.pubber.Pubber - Starting executor with send message delay 2000
[MQTT Call: projects/gcp-account/locations/us-central1/registries/sensor_hub/devices/GAT-001] INFO daq.pubber.Pubber - Sending state message for device GAT-001
[MQTT Call: projects/gcp-account/locations/us-central1/registries/sensor_hub/devices/GAT-001] INFO daq.pubber.Pubber - Sending state message for device GAT-001
[pool-1-thread-1] INFO daq.pubber.Pubber - Sending test message for sensor_hub/GAT-001
[pool-1-thread-1] INFO daq.pubber.Pubber - Sending test message for sensor_hub/GAT-001
&hellip;
</pre>

And an associated bit of activity in the validation output:
<pre>
&hellip;
Success validating out/pointset_GAT-001.json
Success validating out/pointset_GAT-001.json
Success validating out/config_GAT-001.json
Success validating out/pointset_GAT-001.json
Success validating out/state_GAT-001.json
Success validating out/state_GAT-001.json
Success validating out/state_GAT-001.json
Success validating out/pointset_GAT-001.json
Success validating out/state_GAT-001.json
Success validating out/pointset_GAT-001.json
Success validating out/pointset_GAT-001.json
&hellip;
</pre>
