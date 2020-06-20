#!/bin/bash

source testing/test_preamble.sh

echo Aux Tests >> $TEST_RESULTS

# Runs lint checks and some similar things
echo Lint checks | tee -a $TEST_RESULTS
bin/check_style
echo check_style exit code $? | tee -a $TEST_RESULTS

# Function to create pubber config files (for use in cloud tests)

function make_pubber {
    device=$1
    faux=$2
    fail=$3
    gateway=$4
    local_dir=inst/faux/$faux/local/
    echo Creating $device with $fail/$gateway in $local_dir
    mkdir -p $local_dir
    if [ "$gateway" == null ]; then
        cp resources/test_site/devices/$device/rsa_private.pkcs8 $local_dir
    else
        gateway_dir=$(sh -c "echo $gateway")
        cp resources/test_site/devices/$gateway_dir/rsa_private.pkcs8 $local_dir
    fi
    cat <<EOF > $local_dir/pubber.json
  {
    "projectId": "$project_id",
    "cloudRegion": $cloud_region,
    "registryId": $registry_id,
    "extraField": $fail,
    "gatewayId": $gateway,
    "deviceId": "$device"
  }
EOF
  ls -l $local_dir
}

function capture_test_results {
    module_name=$1
    fgrep -h RESULT inst/run-port-*/nodes/$module_name*/tmp/report.txt | tee -a $TEST_RESULTS
}

# Setup an instance test site
rm -rf inst/test_site && mkdir -p inst/test_site
cp -a resources/test_site inst/

echo %%%%%%%%%%%%%%%%%%%%%%%%% Preparing aux test run
mkdir -p local/site
cp -r resources/test_site/device_types/rocket local/site/device_types/
mkdir -p local/site/device_types/rocket/aux/
cp subset/bacnet/bacnetTests/src/main/resources/pics.csv local/site/device_types/rocket/aux/
cp -r resources/test_site/mac_addrs local/site/
cat <<EOF > local/system.yaml
---
include: config/system/all.conf
finish_hook: bin/dump_network
test_config: resources/runtime_configs/long_wait
site_path: inst/test_site
schema_path: schemas/udmi
interfaces:
  faux-1:
    opts: brute broadcast_client
  faux-2:
    opts: nobrute expiredtls bacnetfail pubber passwordfail opendns
  faux-3:
    opts: tls macoui passwordpass bacnet pubber ntp_client broadcast_client
long_dhcp_response_sec: 0
monitor_scan_sec: 0
EOF

if [ -f "$gcp_cred" ]; then
    echo Using credentials from $gcp_cred
    echo gcp_cred: $gcp_cred >> local/system.yaml
    project_id=`jq -r .project_id $gcp_cred`

    cloud_file=inst/test_site/cloud_iot_config.json
    echo Pulling cloud iot details from $cloud_file...
    registry_id=`jq .registry_id $cloud_file`
    cloud_region=`jq .cloud_region $cloud_file`

    make_pubber AHU-1 daq-faux-2 null null
    make_pubber SNS-4 daq-faux-3 1234 \"GAT-123\"

    GOOGLE_APPLICATION_CREDENTIALS=$gcp_cred bin/registrar $project_id
    cat inst/test_site/registration_summary.json | tee -a $GCP_RESULTS
    echo | tee -a $GCP_RESULTS
    fgrep hash inst/test_site/devices/*/metadata_norm.json | tee -a $GCP_RESULTS
    find inst/test_site -name errors.json | tee -a $GCP_RESULTS
    more inst/test_site/devices/*/errors.json
else
    echo No gcp service account defined, as required for cloud-based tests.
    echo Please check install/setup documentation to enable.
fi

more inst/faux/daq-faux-*/local/pubber.json | cat

echo Build all container images...
cmd/build

echo %%%%%%%%%%%%%%%%%%%%%%%%% Starting aux test run
cmd/run -s

# Capture RESULT lines from ping activation logs (not generated report).
fgrep -h RESULT inst/run-port*/nodes/ping*/activate.log \
    | sed -e 's/\s*\(%%.*\)*$//' | tee -a $TEST_RESULTS

# Add the RESULT lines from all aux test report files.
capture_test_results bacext
capture_test_results macoui
capture_test_results tls
capture_test_results password
capture_test_results discover
capture_test_results network

# Capture peripheral logs
more inst/run-port-*/scans/ip_triggers.txt | cat
dhcp_done=$(fgrep done inst/run-port-01/scans/ip_triggers.txt | wc -l)
dhcp_long=$(fgrep long inst/run-port-01/scans/ip_triggers.txt | wc -l)
echo dhcp requests $((dhcp_done > 1)) $((dhcp_done < 3)) \
     $((dhcp_long > 1)) $((dhcp_long < 4)) | tee -a $TEST_RESULTS
sort inst/result.log | tee -a $TEST_RESULTS

# Show partial logs from each test
head inst/gw*/nodes/gw*/activate.log
head inst/run-port-*/nodes/*/activate.log
head inst/run-port-*/nodes/*/tmp/report.txt
ls inst/run-port-01/finish/fail01/ | tee -a $TEST_RESULTS

# Add the port-01 and port-02 module config into the file
echo port-01 module_config modules | tee -a $TEST_RESULTS
jq .modules inst/run-port-01/nodes/ping01/tmp/module_config.json | tee -a $TEST_RESULTS
echo port-02 module_config modules | tee -a $TEST_RESULTS
jq .modules inst/run-port-02/nodes/ping02/tmp/module_config.json | tee -a $TEST_RESULTS

# Add a lovely snake and a lizard into this file for testing device/type mappings.
cat inst/run-port-03/nodes/ping03/tmp/snake.txt | tee -a $TEST_RESULTS
cat inst/run-port-03/nodes/ping03/tmp/lizard.txt | tee -a $TEST_RESULTS

# Add the results for cloud tests into a different file, since cloud tests may not run if
# our test environment isn't set up correctly. See bin/test_daq for more insight.
fgrep -h RESULT inst/run-port-*/nodes/udmi*/tmp/report.txt | tee -a $GCP_RESULTS

for num in 1 2 3; do
    echo docker logs daq-faux-$num
    docker logs daq-faux-$num 2>&1 | head -n 100
done
echo done with docker logs

echo Raw generated report:
cat inst/reports/report_9a02571e8f01_*.md
echo End generated report.

# Make sure that what you've done hasn't messed up DAQ by diffing the output from your test run
cat docs/device_report.md | redact > out/redacted_docs.md
cp inst/reports/report_9a02571e8f01_*.md out/
cat inst/reports/report_9a02571e8f01_*.md | redact > out/redacted_file.md

fgrep Host: out/redacted_file.md | tee -a $TEST_RESULTS

echo Redacted docs diff | tee -a $TEST_RESULTS
(diff out/redacted_docs.md out/redacted_file.md && echo No report diff) \
    | tee -a $TEST_RESULTS

# Make sure there's no file pollution from the test run.
git status --porcelain | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%%%%% Preparing hold test run
# Try various exception handling conditions.
cat <<EOF > local/system.yaml
---
include: config/system/multi.conf
fail_module:
  ping_01: finalize
  hold_02: initialize
  ping_03: callback
EOF

function kill_gateway {
    GW=$1
    pid=$(ps ax | fgrep tcpdump | fgrep $GW-eth0 | fgrep -v docker | fgrep -v /tmp/ | awk '{print $1}')
    echo Killing $GW-eth dhcp tcpdump pid $pid
    kill $pid
}

# Check that killing the dhcp monitor aborts the run.
MARKER=inst/run-port-03/nodes/hold03/activate.log
monitor_marker $MARKER "kill_gateway gw03"

echo %%%%%%%%%%%%%%%%%%%%%%%%% Starting hold test run
cmd/run -k -s finish_hook=bin/dump_network

cat inst/result.log | sort | tee -a $TEST_RESULTS
find inst/ -name activate.log | sort | tee -a $TEST_RESULTS
head inst/run-port-*/nodes/nmap*/activate.log
head inst/run-port-*/finish/nmap*/*

tcpdump -en -r inst/run-port-01/scans/test_nmap.pcap icmp or arp


# Check port toggling does not cause a shutdown
cat <<EOF > local/system.yaml
---
include: config/system/base.yaml
port_flap_timeout_sec: 10
port_debounce_sec: 0
EOF
monitor_log "Port 1 dpid 2 is now active" "sudo ifconfig faux down;sleep 5; sudo ifconfig faux up"
monitor_log "Target port 1 test hold running" "sudo ifconfig faux down"
cmd/run -s -k
disconnections=$(cat inst/cmdrun.log | grep "Port 1 dpid 2 is now inactive" | wc -l)
echo Enough port disconnects: $((disconnections >= 2)) | tee -a $TEST_RESULTS
cat inst/result.log | sort | tee -a $TEST_RESULTS
echo Done with tests | tee -a $TEST_RESULTS
