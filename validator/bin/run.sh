#!/bin/bash -e

ROOT=$(dirname $0)/../..
cd $ROOT

jarfile=validator/build/libs/validator-1.0-SNAPSHOT-all.jar

if [ -z "$1" -o -z "$2" ]; then
    echo Usage: $0 [schema] [target]
    false
fi

schema=$1
target=$2
ignoreset=$3

if [ ! -f $jarfile ]; then
    echo Building validator...
    validator/bin/build.sh
fi

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
absjar=$(realpath $jarfile)
(cd $schemadir; java -jar $absjar $schemafile $target $ignoreset) || error=$?

echo Validation complete, exit $error
exit $error
