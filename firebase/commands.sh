#!/bin/bash -e

echo Deploy: firebase deploy --only functions
echo Test: firebase serve --only hosting
echo Pull: gcloud pubsub subscriptions pull --auto-ack daq_monitor
echo DB: https://firebase.corp.google.com/project/bos-daq-testing/database/firestore/data~2F
