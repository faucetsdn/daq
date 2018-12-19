#!/bin/bash -e

PROJECT=$(gcloud config list --format 'value(core.project)' 2>/dev/null)

if [ -z "$PROJECT" ]; then
    echo No cloud project configured.
    false
fi

echo Configured for cloud project $PROJECT
echo Deploy: firebase deploy --only functions
echo Test: firebase serve --only hosting
echo Pull: gcloud pubsub subscriptions pull --auto-ack daq_monitor
echo DB: https://console.cloud.google.com/firestore/data/?project=$PROJECT
echo Host: https://$PROJECT.firebaseapp.com
