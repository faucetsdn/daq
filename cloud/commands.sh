#!/bin/bash -e

echo Deploy: firebase deploy --only functions
echo Pull: gcloud pubsub subscriptions pull --auto-ack daq_monitor

