#!/bin/bash -e

bin/build.sh

java -jar build/libs/pubber-1.0-SNAPSHOT-all.jar ../config/
