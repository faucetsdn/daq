#!/bin/bash -e

ROOT=$(dirname $0)/..
cd $ROOT

jarfile=$(realpath build/libs/validator-1.0-SNAPSHOT-all.jar)

if [ -z "$1" -o -z "$2" ]; then
    echo Usage: $0 [schema] [target]
    false
fi

schema=$1
target=$2
ignoreset=$3

echo Executing validator $schema $target...

schemafile=$(realpath $schema)
if [ -d $schemafile ]; then
    schemadir=$schemafile
    schemafile=.
else
    schemadir=$(dirname $schemafile)
    schemafile=${schemafile#$schemadir/}
    fulltarget=$(realpath $target)
    target=${fulltarget#$schemadir/}
fi

echo Running schema $schemafile in $schemadir

rm -rf $schemadir/out

error=0
(cd $schemadir; java -jar $jarfile $schemafile $target $ignoreset) || error=$?

echo Validation complete, exit $error
exit $error
