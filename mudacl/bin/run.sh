#!/bin/bash -e

ROOT=$(dirname $0)/..

# Runtime switch configuration.
SWITCH_TOPOLOGY=inst/faucet.yaml

# Set of available mud files.
MUD_DIR=mud_files/

# Device topology specific to local setup.
DEVICE_TOPOLOGY=local/devices.json

# Device type mapping, specific to local setup.
DEVICE_TYPES=local/types.json

# Output directory for runtime ACLs.
OUTPUT_DIR=inst/port_acls/

(cd $ROOT; ./gradlew shadow)

echo
echo Executing mudacl generator...

java -jar $ROOT/build/libs/mudacl-1.0-SNAPSHOT-all.jar $SWITCH_TOPOLOGY $DEVICE_TOPOLOGY $DEVICE_TYPES $MUD_DIR $OUTPUT_DIR

ls -l $OUTPUT_DIR
