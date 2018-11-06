#!/bin/bash -e

PROJECT=$(gcloud config list --format 'value(core.project)' 2>/dev/null)

if [ -z "$PROJECT" ]; then
    echo No cloud project configured.
    false
fi

echo Configured for cloud project $PROJECT
echo Set default using: gcloud config set project XXX

firebase deploy --only functions --project $PROJECT

echo For local hosting: firebase serve --only hosting --project $PROJECT
echo Subscription pull: gcloud pubsub subscriptions pull --auto-ack daq_monitor --project $PROJECT
echo Firestore address: https://console.cloud.google.com/firestore/data/?project=$PROJECT
echo Application host : https://$PROJECT.firebaseapp.com
