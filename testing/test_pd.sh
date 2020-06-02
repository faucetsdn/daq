#!/bin/bash

source testing/test_preamble.sh
cmd/build

# Check port toggling does not cause a shutdown
cat <<EOF > local/system.yaml
---
include: misc/system_base.yaml
port_flap_timeout_sec: 10
port_debounce_sec: 0
EOF
for i in {1..10}; do
    monitor_log "Port 1 dpid 2 is now active" "sudo ifconfig faux down;sleep 5; sudo ifconfig faux up"
    monitor_log "Target port 1 test hold running" "sudo ifconfig faux down"
    cmd/run -s -k
    disconnections=$(cat inst/cmdrun.log | grep "Port 1 dpid 2 is now inactive" | wc -l)
    echo Enough port disconnects: $((disconnections >= 2)) | tee -a $TEST_RESULTS
    cat inst/result.log | sort | tee -a $TEST_RESULTS
done
echo Done with tests | tee -a $TEST_RESULTS
