#!/bin/bash -e

ROOT=$(dirname $0)/../..
cd $ROOT

jarfile=validator/build/libs/validator-1.0-SNAPSHOT-all.jar
mainclass=com.google.daq.mqtt.registrar.Registrar

if [ -z "$1" -o -z "$2" ]; then
    echo Usage: $0 [config_file] [devices_dir]
    false
fi

config_file=$1
devices_dir=$2
schema_dir=$3

echo Using gcp credentials $config_file
echo Using site config dir $devices_dir
echo Using schema root dir $schema_dir

JAVA=/usr/lib/jvm/java-8-openjdk-amd64/bin/java

error=0
$JAVA -cp $jarfile $mainclass $config_file $devices_dir $schema_dir || error=$?

echo Registrar complete, exit $error
exit $error
