#!/bin/bash -e

if [ $# != 1 ]; then
    echo Usage: $0 [project_id]
    false
fi

ROOT=$(realpath $(dirname $0)/..)
cd $ROOT

source etc/config_base.sh

PROJECT=$1
shift

CFILE=$PROJECT.js

echo
echo For local hosting: firebase serve --only hosting --project $PROJECT
echo Subscription pull: gcloud pubsub subscriptions pull --auto-ack daq_monitor --project $PROJECT
echo Firestore address: https://console.cloud.google.com/firestore/data/?project=$PROJECT
echo Application host : https://$PROJECT.firebaseapp.com
echo

if [ -f local/$CFILE ]; then
    echo Copying local/$CFILE to firebase/public/firebase_config.js
    cp local/$CFILE firebase/public/firebase_config.js
else
    echo No local/$CFILE firebase configuration found.
    false
fi

cd firebase

version=`git describe --dirty`
echo Deploying version $version to $PROJECT
echo "const daq_deploy_version = '$version';" > public/deploy_version.js

echo firebase deploy --project $PROJECT
firebase deploy --project $PROJECT
