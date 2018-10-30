#!/bin/bash -e

rundir=$(dirname $0)
cd $rundir/..

echo Running in $PWD

rm -rf build

#mkdir -p build/libs
#(cd datafmt; ../gradlew build)

./gradlew build
./gradlew shadow
cp datafmt/build/libs/* build/libs/
