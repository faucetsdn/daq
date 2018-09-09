#!/bin/bash -e

ROOT=$(dirname $0)/..

cd $ROOT
rm -rf out
mkdir -p out
./gradlew shadow
