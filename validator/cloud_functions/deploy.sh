#!/bin/bash -e

PROJECT=$1

if [ -z "$PROJECT" ]; then
    echo $0 [project_id]
    false
fi


gcloud functions deploy udmi_firebase --project $PROJECT --runtime nodejs8 \
       --trigger-resource target --trigger-event google.pubsub.topic.publish

gcloud functions deploy udmi_state --project $PROJECT --runtime nodejs8 \
       --trigger-resource state --trigger-event google.pubsub.topic.publish
