#!/bin/bash -e

# Input state topic to monitor. Output topic is defined in the code itself.
TOPIC=state
FUNC=state_shunt
PROJECT=$1

if [ -z "$PROJECT" ]; then
    echo $0 [project_id]
    false
fi


gcloud functions deploy $FUNC --project $PROJECT --runtime nodejs8 \
       --trigger-resource $TOPIC --trigger-event google.pubsub.topic.publish
