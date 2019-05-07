#!/bin/bash -e

if [ $# != 1 ]; then
    echo Usage: $0 [project_id]
    false
fi

PROJECT=$1

echo For local hosting: firebase serve --only hosting --project $PROJECT
echo Subscription pull: gcloud pubsub subscriptions pull --auto-ack daq_monitor --project $PROJECT
echo Firestore address: https://console.cloud.google.com/firestore/data/?project=$PROJECT
echo Application host : https://$PROJECT.firebaseapp.com
echo
echo Running firebase deploy --only functions --project $PROJECT
firebase deploy --only functions --project $PROJECT
