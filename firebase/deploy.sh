#!/bin/bash -e

ROOT=$(realpath $(dirname $0)/..)
cd $ROOT

source misc/config_base.sh

if [ -z "$gcp_cred" ]; then
    echo gcp_cred not defined in system configuration.
    false
fi

PROJECT=`jq .project_id $gcp_cred`
if [ -z "$PROJECT" ]; then
    echo project_id not extracted from $gcp_cred.
    false
fi

CFILE=firebase_config.js

echo
echo For local hosting: firebase serve --only hosting --project $PROJECT
echo Subscription pull: gcloud pubsub subscriptions pull --auto-ack daq_monitor --project $PROJECT
echo Firestore address: https://console.cloud.google.com/firestore/data/?project=$PROJECT
echo Application host : https://$PROJECT.firebaseapp.com
echo

if [ -f firebase/public/$CFILE ]; then
    echo Using existing firebase/public/$CFILE
elif [ -f local/$CFILE ]; then
    echo Copying local/$CFILE to firebase/public/
    cp local/$CFILE firebase/public/
else
    echo No local/$CFILE found.
    false
fi

cd firebase

echo firebase deploy --project $PROJECT
firebase deploy --project $PROJECT
