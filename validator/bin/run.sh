#!/bin/bash -e

ROOT=$(dirname $0)/..
cd $ROOT

if [ -z "$1" -o -z "$2" ]; then
    echo Usage: $0 [schema] [target]
    false
fi

schema=$1
target=$2

bin/build.sh

echo Executing validator $schema $target...

error=0
java -jar build/libs/validator-1.0-SNAPSHOT-all.jar $schema $target || error=$?

echo Validation complete, exit $error
exit $error
