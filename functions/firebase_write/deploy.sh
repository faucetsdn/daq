#!/bin/bash -e

TOPIC=target
FUNC=device_event
PROJECT=$1

if [ -z "$PROJECT" ]; then
    echo $0 [project_id]
    false
fi


gcloud functions deploy $FUNC --project $PROJECT --runtime nodejs8 \
       --trigger-resource $TOPIC --trigger-event google.pubsub.topic.publish
