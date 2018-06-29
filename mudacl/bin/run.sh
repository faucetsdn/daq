#!/bin/bash -e

CONFIG_ROOT=site/test
SWITCH_TOPOLOGY=$CONFIG_ROOT/faucet.yaml
DEVICE_TOPOLOGY=$CONFIG_ROOT/devices.json
DEVICE_TYPES=$CONFIG_ROOT/types.json
MUD_DIR=$CONFIG_ROOT/mud_files/
OUTPUT_DIR=$CONFIG_ROOT/port_acls/

if [ ! -f gradlew ]; then
    echo Please run in the daq/mudacl directory.
    false
fi

./gradlew shadow

echo
echo Execution mudacl generator on $CONFIG_ROOT...

java -jar build/libs/mudacl-1.0-SNAPSHOT-all.jar $SWITCH_TOPOLOGY $DEVICE_TOPOLOGY $DEVICE_TYPES $MUD_DIR $OUTPUT_DIR

echo Success!




