#!/bin/bash -e

ROOT=$(dirname $0)/..

cd $ROOT
rm -rf build
./gradlew shadow
