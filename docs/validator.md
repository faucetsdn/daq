# Validator Setup

The `validator` is a sub-component of DAQ that can be used to validate JSON files or stream against a schema
defined by the standard [JSON Schema](https://json-schema.org/) format. There's a couple of different
ways to run the validator, outlined below.

## Local File Validation

Local file validation runs the code against a set of local schemas and inputs.
Specifying a directory, rather than a specific schema or input, will run against the entire set.
An output file is generated that has details about the schema validation result.

<pre>
~/daq/validator$ <b>bin/run.sh schemas/simple.json schemas/simple/simple.json</b>

BUILD SUCCESSFUL in 0s
2 actionable tasks: 2 up-to-date
Executing validator schemas/simple.json schemas/simple/simple.json...
Validation complete, exit 0
</pre>

## Integration Testing

<pre>
~/daq/validator$ <b>bin/test.sh</b>

BUILD SUCCESSFUL in 0s
2 actionable tasks: 2 up-to-date
Testing simple.json against schemas/simple/error.json result 2
Testing simple.json against schemas/simple/simple.json result 0
Testing simple.json against schemas/simple/telemetry.json result 2
Testing state.json against schemas/state/proposal_v1.json result 0
Testing target.json against schemas/target/atmosphere.json result 2
Testing target.json against schemas/target/fcu_01_sw_13.json result 2
Testing target.json against schemas/target/proposal_v1.json result 0
Testing target.json against schemas/target/tce01_01_ne.json result 2
Done with validation.
</pre>

## PubSub Stream Validation

Streaming validation validates a stream of messages pulled from a GCP PuBSub topic. There are three values required
in the `local/system.conf` file to make it work:
* `gcp_cred`: The service account credentials, as per the general [DAQ Firebase setup](firebase.md).
* `gcp_topic`: The PubSub topic name (the thing at the end of `projects/{project-name}/topics/` from the project PubSub setup).
* `gcp_schema`: Indicates which schema to validate against.

You will need to add full Project Editor permissions for the service account.
E.g., to validate messages on the `projects/gcp-account/topics/telemetry` topic, there should be something like:

<pre>
~/daq$ <b>fgrep gcp_ local/system.conf</b>
gcp_cred=local/gcp-account-ce6716521378.json
gcp_topic=telemetry
gcp_schema=validator/schemas/target.json
</pre>

Running the `daq/bin/validate` script will will pull values from the configuration file and automatically start
verifying against the indicated schema. The execution output has a link to a location in the Firestore setup
where schema results will be stored.

<pre>
~/daq$ <b>bin/validate</b>
Using credentials from /home/user/daq/local/gcp-account-ce6716521378.json

BUILD SUCCESSFUL in 0s
2 actionable tasks: 2 up-to-date

Executing validator schemas/telemetry.json pubsub:telmetry...
Connecting to pubsub topic telmetry
Results will be uploaded to https://console.cloud.google.com/firestore/data/registries/primary/devices/device_one/validations/target?project=daq-project
Entering pubsub message loop on projects/gcp-account/subscriptions/daq-validator
Error validating /home/user/daq/validator/out/message_TCE01$2d04$20NW$20Controls.json: DeviceId TCE01$2d04$20NW$20Controls must match pattern [a-zA-Z]+[a-zA-Z0-9_]+[a-zA-Z0-9]+
Error validating /home/user/daq/validator/out/message_TCE01$2d04$20NW$20Controls.json: DeviceId TCE01$2d04$20NW$20Controls must match pattern [a-zA-Z]+[a-zA-Z0-9_]+[a-zA-Z0-9]+
<em>...</em>
</pre>

