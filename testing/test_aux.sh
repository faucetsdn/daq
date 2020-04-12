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
    mkdir -p inst/faux/$faux/local/
    cp misc/test_site/devices/$device/rsa_private.pkcs8 inst/faux/$faux/local/
    cat <<EOF > inst/faux/$faux/local/pubber.json
  {
    "projectId": $project_id,
    "cloudRegion": $cloud_region,
    "registryId": $registry_id,
    "extraField": $fail,
    "deviceId": "$device"
  }
EOF
}

function capture_test_results {
    module_name=$1
    fgrep -h RESULT inst/run-port-*/nodes/$module_name*/tmp/report.txt | tee -a $TEST_RESULTS
}

# Setup an instance test site
rm -rf inst/test_site && mkdir -p inst/test_site
cp -a misc/test_site inst/

echo Extended tests | tee -a $TEST_RESULTS
mkdir -p local/site
cp -r misc/test_site/device_types/rocket local/site/device_types/
mkdir -p local/site/device_types/rocket/aux/
cp subset/bacnet/bacnetTests/src/main/resources/pics.csv local/site/device_types/rocket/aux/
cp -r misc/test_site/mac_addrs local/site/
cp misc/system_all.conf local/system.conf
cat <<EOF >> local/system.conf
fail_hook=misc/dump_network.sh
site_path=inst/test_site
startup_faux_1_opts="brute broadcast_client"
startup_faux_2_opts="nobrute expiredtls bacnetfail pubber passwordfail"
startup_faux_3_opts="tls macoui passwordpass bacnet pubber ntp_client broadcast_client"
long_dhcp_response_sec=0
monitor_scan_sec=0
EOF

if [ -f $cred_file ]; then
    echo Using credentials from $cred_file
    echo gcp_cred=$cred_file >> local/system.conf
    project_id=`jq .project_id $cred_file`

    cloud_file=inst/test_site/cloud_iot_config.json
    echo Pulling cloud iot details from $cloud_file...
    registry_id=`jq .registry_id $cloud_file`
    cloud_region=`jq .cloud_region $cloud_file`

    make_pubber AHU-1 daq-faux-2 null
    make_pubber SNS-4 daq-faux-3 1234
else
    echo No gcp service account defined, as required for cloud-based tests.
    echo Please check install/setup documentation to enable.
fi

more inst/faux/daq-faux-*/local/pubber.json | cat

echo Build all container images...
cmd/build inline

echo Starting aux test run...
cmd/run -s

# Add the RESULT lines from all aux tests (from all ports, 3 in this case) into a file.
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

# Show the full logs from each test
#more inst/gw*/nodes/gw*/activate.log | cat
#more inst/run-port-*/nodes/*/activate.log | cat
#more inst/run-port-*/nodes/*/tmp/report.txt | cat

ls inst/fail_fail01/ | tee -a $TEST_RESULTS

# Add the results for cloud tests into a different file, since cloud tests may not run if
# our test environment isn't set up correctly. See bin/test_daq for more insight.
fgrep -h RESULT inst/run-port-*/nodes/udmi*/tmp/report.txt | tee -a $GCP_RESULTS

for num in 1 2 3; do
    echo docker logs daq-faux-$num
    docker logs daq-faux-$num | head -n 100
done
echo done with docker logs

# Make sure that what you've done hasn't messed up DAQ by diffing the output from your test run
cat docs/device_report.md | redact > out/redacted_docs.md
cp inst/reports/report_9a02571e8f01_*.md out/
cat inst/reports/report_9a02571e8f01_*.md | redact > out/redacted_file.md

fgrep Host: out/redacted_file.md | tee -a $TEST_RESULTS

#more inst/fail_*/* | cat

# Try various exception handling conditions.
cp misc/system_multi.conf local/system.conf
cat <<EOF >> local/system.conf
ex_hold_01=initialize
ex_ping_02=finalize
ex_ping_03=callback
EOF


# Wait until the stalled ping test has been activated, and then kill dhcp on that gateway.
MARKER2=inst/run-port-02/nodes/hold02/activate.log
MARKER3=inst/run-port-03/nodes/hold03/activate.log
function cleanup_marker {
    mkdir -p ${MARKER2%/*}
    touch $MARKER2 $MARKER3
}
trap cleanup_marker EXIT

function monitor_marker {
    MARKER=$1
    rm -f $MARKER
    while [ ! -f $MARKER ]; do
        echo test_aux.sh waiting for $MARKER
        sleep 60
    done
    ps ax | fgrep tcpdump | fgrep gw02-eth0 | fgrep -v docker | fgrep -v /tmp/
    pid=$(ps ax | fgrep tcpdump | fgrep gw02-eth0 | fgrep -v docker | fgrep -v /tmp/ | awk '{print $1}')
    echo $MARKER found, killing gw02-eth dhcp tcpdump pid $pid
    kill $pid
}

monitor_marker $MARKER2 &
monitor_marker $MARKER3 &

cmd/run -k -s

cat inst/result.log | sort | tee -a $TEST_RESULTS
find inst/ -name activate.log | sort | tee -a $TEST_RESULTS
#more inst/run-port-*/nodes/*/activate.log | cat

echo Done with tests | tee -a $TEST_RESULTS
