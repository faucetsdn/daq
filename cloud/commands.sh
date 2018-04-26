#!/bin/bash -e

echo Deploy: firebase deploy --only functions
echo Test: curl https://us-central1-bos-daq-testing.cloudfunctions.net/addMessage?text=world

