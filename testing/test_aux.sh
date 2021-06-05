#!/bin/bash

source testing/test_preamble.sh

echo Aux Tests >> $TEST_RESULTS

# Function to create pubber config files (for use in cloud tests)

function make_pubber {
    device=$1
    mac_addr=$2
    faux=$3
    extra=$4
    gateway=$5
    serial_no=test_aux-$RANDOM
    local_dir=inst/faux/$faux/local/
    echo Creating $device with $extra/$gateway in $local_dir
    mkdir -p $local_dir
    if [ "$gateway" == null ]; then
        cp resources/test_site/devices/$device/rsa_private.pkcs8 $local_dir
    else
        gateway_dir=$(sh -c "echo $gateway")
        cp resources/test_site/devices/$gateway_dir/rsa_private.pkcs8 $local_dir
    fi

    device_file=inst/test_site/mac_addrs/$mac_addr/device_config.json
    echo Updating $device_file with $serial_no
    jq ".device_info.serial = \"$serial_no\"" $device_file > $device_file.tmp
    mv $device_file.tmp $device_file

    cat <<EOF > $local_dir/pubber.json
  {
    "projectId": "$project_id",
    "cloudRegion": "$cloud_region",
    "registryId": "$registry_id",
    "extraField": $extra,
    "serialNo": "$serial_no",
    "macAddr": "$mac_addr",
    "keyFile": "local/rsa_private.pkcs8",
    "gatewayId": $gateway,
    "deviceId": "$device"
  }
EOF
  ls -l $local_dir
}

function setup_reflector {
    echo Setting up GCP reflector configuration...

    cat <<EOF > inst/config/gcp_reflect_config.json
  {
    "project_id": "$project_id",
    "registry_id": "$registry_id"
  }
EOF
}

function capture_test_results {
    module_name=$1
    for mac in 9a02571e8f01 3c5ab41e8f0b 3c5ab41e8f0a; do
      fgrep -h 'RESULT ' inst/run-$mac/nodes/$module_name*/tmp/report.txt | tee -a $TEST_RESULTS
    done
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
# Create config for the password test to select which dictionaries to use.
cat <<EOF > local/base_config.json
{
  "include": "../resources/setups/baseline/base_config.json",
  "modules": {
    "password": {
      "dictionary_dir": "resources/faux"
    }
  }
}
EOF

cat <<EOF > local/system.yaml
---
include: ../config/system/all.conf
base_conf: local/base_config.json
finish_hook: bin/dump_network
test_config: resources/runtime_configs/long_wait
site_path: inst/test_site
schema_path: schemas/udmi
interfaces:
  faux-1:
    opts: brute broadcast_client ntpv4 wpa
  faux-2:
    opts: nobrute expiredtls bacnetfail pubber passwordfail ntpv3 opendns ssh curl wpawrong
  faux-3:
    opts: tls macoui passwordpass bacnet pubber broadcast_client ssh curl
long_dhcp_response_sec: 0
monitor_scan_sec: 20
EOF

if [ -f "$gcp_cred" ]; then
    echo Using credentials from $gcp_cred
    echo gcp_cred: $gcp_cred >> local/system.yaml
    project_id=`jq -r .project_id $gcp_cred`

    cloud_file=inst/test_site/cloud_iot_config.json
    echo Pulling cloud iot details from $cloud_file...
    registry_id=`jq -r .registry_id $cloud_file`
    cloud_region=`jq -r .cloud_region $cloud_file`

    make_pubber AHU-1 3c5ab41e8f0b daq-faux-2 null null
    make_pubber SNS-4 3c5ab41e8f0a daq-faux-3 1234 \"GAT-123\"

    GOOGLE_APPLICATION_CREDENTIALS=$gcp_cred udmi/bin/registrar inst/test_site $project_id
    cat inst/test_site/registration_summary.json | redact | tee -a $GCP_RESULTS
    echo | tee -a $GCP_RESULTS
    fgrep hash inst/test_site/devices/*/metadata_norm.json | tee -a $GCP_RESULTS
    find inst/test_site -name errors.json | tee -a $GCP_RESULTS
    more inst/test_site/devices/*/errors.json

    setup_reflector
else
    echo No gcp service account defined, as required for cloud-based tests.
    echo Please check install/setup documentation to enable.
fi

more inst/faux/daq-faux-*/local/pubber.json | cat

echo Build all container images...
cmd/build missing

image_count=$(docker images -q | wc -l)
echo Built $image_count docker images.

echo %%%%%%%%%%%%%%%%%%%%%%%%% Starting aux test run
cmd/run -s

# Capture RESULT lines from ping activation logs (not generated report).
for mac in 9a02571e8f01 3c5ab41e8f0b 3c5ab41e8f0a; do
  fgrep -h 'RESULT ' inst/run-$mac/nodes/ping*/activate.log \
    | sed -e 's/\s*\(%%.*\)*$//' | tee -a $TEST_RESULTS
done

# Add the RESULT lines from all aux test report files.
capture_test_results bacext
capture_test_results tls
capture_test_results password
capture_test_results discover
capture_test_results network
capture_test_results dot1x

# Capture peripheral logs
more inst/run-*/scans/ip_triggers.txt | cat
dhcp_done=$(fgrep done inst/run-9a02571e8f01/scans/ip_triggers.txt | wc -l)
dhcp_long=$(fgrep long inst/run-9a02571e8f01/scans/ip_triggers.txt | wc -l)
echo dhcp requests $((dhcp_done > 1)) $((dhcp_done < 3)) \
     $((dhcp_long >= 1)) $((dhcp_long < 4)) | tee -a $TEST_RESULTS
sort inst/result.log | tee -a $TEST_RESULTS

# Show partial logs from each test
head -20 inst/gw*/nodes/gw*/activate.log
head -20 inst/run-*/nodes/*/activate.log
head -20 inst/run-*/nodes/*/tmp/report.txt
ls inst/run-9a02571e8f01/finish/fail*/ | tee -a $TEST_RESULTS

# Add the port-01 and port-02 module config into the file
echo port-01 module_config modules | tee -a $TEST_RESULTS
jq .modules inst/run-9a02571e8f01/nodes/ping*/tmp/module_config.json | tee -a $TEST_RESULTS
echo port-02 module_config modules | tee -a $TEST_RESULTS
jq .modules inst/run-3c5ab41e8f0b/nodes/ping*/tmp/module_config.json | tee -a $TEST_RESULTS

# Add a lovely snake and a lizard into this file for testing device/type mappings.
cat inst/run-3c5ab41e8f0a/nodes/ping*/tmp/snake.txt | tee -a $TEST_RESULTS
cat inst/run-3c5ab41e8f0a/nodes/ping*/tmp/lizard.txt | tee -a $TEST_RESULTS

# Add the results for cloud tests into a different file, since cloud tests may not run if
# our test environment isn't set up correctly. See bin/test_daq for more insight.
fgrep -h 'RESULT ' inst/run-*/nodes/udmi*/tmp/report.txt | redact | tee -a $GCP_RESULTS

# Check that configuration is properly mapped into the container.
fgrep 'Config contains' inst/run-*/nodes/udmi*/activate.log | tee -a $TEST_RESULTS

echo Full UDMI testing logs
more inst/run-*/nodes/udmi*/activate.log | cat

for num in 1 2 3; do
    echo docker logs daq-faux-$num
    docker logs daq-faux-$num 2>&1 | head -n 500
done
echo docker logs done

echo Raw generated report:
cat inst/reports/report_9a02571e8f01_*.md
echo End generated report.

# Make sure that what you've done hasn't messed up DAQ by diffing the output from your test run
cat docs/device_report.md | redact > out/redacted_docs.md
cp inst/reports/report_9a02571e8f01_*.md out/
cat inst/reports/report_9a02571e8f01_*.md | redact > out/redacted_file.md

fgrep Host: out/redacted_file.md | tee -a $TEST_RESULTS

echo Redacted docs diff | tee -a $TEST_RESULTS
diff out/redacted_docs.md out/redacted_file.md > out/redacted_file.diff
cat -vet out/redacted_file.diff | tee -a $TEST_RESULTS
diff_lines=`cat out/redacted_file.diff | wc -l`
if [ $diff_lines == 0 ]; then
    echo No report diff | tee -a $TEST_RESULTS
fi

# Make sure there's no file pollution from the test run.
git status --porcelain | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%%%%% Preparing hold test run
# Try various exception handling conditions.
cat <<EOF > local/system.yaml
---
include: ../config/system/multi.conf
fail_module:
  ping_9a02571e8f01: finalize
  hold_9a02571e8f02: initialize
  ping_9a02571e8f03: callback
EOF

function kill_gateway {
    GW=$1
    pid=$(ps ax | fgrep tcpdump | fgrep $GW-eth0 | fgrep -v docker | fgrep -v /tmp/ | awk '{print $1}')
    echo Killing $GW-eth dhcp tcpdump pid $pid
    kill $pid
}

# Check that killing the dhcp monitor aborts the run.
MARKER=inst/run-9a02571e8f03/nodes/hold*/activate.log
monitor_marker $MARKER "kill_gateway gw03"

echo %%%%%%%%%%%%%%%%%%%%%%%%% Starting hold test run
rm -r inst/run-*
cmd/run -k -s finish_hook=bin/dump_network

cat inst/result.log | sort | tee -a $TEST_RESULTS
head inst/run-*/nodes/nmap*/activate.log
head inst/run-*/finish/nmap*/*

tcpdump -en -r inst/run-9a02571e8f01/scans/test_nmap.pcap icmp or arp

echo %%%%%%%%%%%%%%%%%%%%%%%%% Running port toggle test
# Check port toggling does not cause a shutdown
cat <<EOF > local/system.yaml
---
include: ../config/system/base.yaml
port_flap_timeout_sec: 20
port_debounce_sec: 0
EOF
monitor_log "Port 1 dpid 2 is now active" "sudo ifconfig faux down;sleep 15; sudo ifconfig faux up"
monitor_log "Target device 9a02571e8f00 test hold running" "sudo ifconfig faux down"
rm -r inst/run-*
cmd/run -s -k
disconnections=$(cat inst/daq.log | grep "Port 1 dpid 2 is now inactive" | wc -l)
echo Enough port disconnects: $((disconnections >= 2)) | tee -a $TEST_RESULTS
cat inst/result.log | sort | tee -a $TEST_RESULTS
echo Done with tests | tee -a $TEST_RESULTS
