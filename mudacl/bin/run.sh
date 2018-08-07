#!/bin/bash -e

ROOT=$(dirname $0)/..

# Set of available mud files.
MUD_DIR=mud_files/

# Output directory for runtime ACLs.
TEMPLATE_DIR=inst/acl_templates

(cd $ROOT; ./gradlew shadow)

echo
echo Executing mudacl generator...

java -jar $ROOT/build/libs/mudacl-1.0-SNAPSHOT-all.jar $MUD_DIR $TEMPLATE_DIR
