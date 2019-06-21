#!/bin/bash -e

MUDACL=$(dirname $0)/..

if [ $# != 2 ]; then
    echo Usage: $0 [mud files directory] [acl template directory]
    false
fi

mud_files=$1
acl_templates=$2

(cd $MUDACL; ./gradlew shadow)

echo
echo Executing mudacl generator on $mud_files...

java -jar $MUDACL/build/libs/mudacl-1.0-SNAPSHOT.jar $mud_files $acl_templates
