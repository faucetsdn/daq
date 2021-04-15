#!/bin/bash

source testing/test_preamble.sh

echo MUD Tests >> $TEST_RESULTS

rm -rf inst/tmp_site && mkdir -p inst/tmp_site
cp resources/setups/baseline/report_template.md inst/tmp_site/

echo Creating MUD templates...
bin/mudacl

build_if_not_release

echo %%%%%%%%%%%%%%%%%%%%%% Default MUD | tee -a $TEST_RESULTS
# Except with a default MUD file that blocks the port.
cmd/run -s interfaces.faux.opts=telnet device_specs=resources/device_specs/simple.json
echo DAQ result code $? | tee -a $TEST_RESULTS
cat inst/result.log | tee -a $TEST_RESULTS
fgrep 'security.nmap.ports'  inst/reports/report_9a02571e8f00_*.md | tee -a $TEST_RESULTS
cat inst/run-9a02571e8f00/nodes/nmap01/activate.log

echo %%%%%%%%%%%%%%%%%%%%%% Mud profile tests | tee -a $TEST_RESULTS
rm -f local/system.yaml
cat > local/system.conf << EOF
include=../config/system/muddy.conf
switch_setup.varz_port=9302
EOF

if [ -z `which tcpdump` ]; then
    export PATH=/usr/sbin:$PATH
fi

function test_device_traffic {
    device_num=$1
    peer_num=$((3-device_num))
    device_mac=9a:02:57:1e:8f:0$device_num
    peer_mac=9a:02:57:1e:8f:0$peer_num
    neighbor_mac=9a:02:57:1e:8f:03

    device_traffic="tcpdump -en -r inst/run-9a02571e8f0$device_num/scans/monitor.pcap port 47808"
    device_bfr_peer="$device_traffic and ether src $peer_mac and ether broadcast"
    device_bfr_ngbr="$device_traffic and ether src $neighbor_mac and ether broadcast"
    device_ufr_peer="$device_traffic and ether src $peer_mac and ether dst $device_mac"
    device_ufr_ngbr="$device_traffic and ether src $neighbor_mac and ether dst $device_mac"
    bfr_peer=$($device_bfr_peer | wc -l)
    bfr_ngbr=$($device_bfr_ngbr | wc -l)
    ufr_peer=$($device_ufr_peer | wc -l)
    ufr_ngbr=$($device_ufr_ngbr | wc -l)
    echo device-$device_num $type $((bfr_peer > 2)) $((bfr_ngbr > 0)) $((ufr_peer > 2)) $((ufr_ngbr > 0)) | tee -a $TEST_RESULTS
}

function test_acl_count {
    device_num=$1
    device_mac=9a:02:57:1e:8f:0$device_num

    jq_filter=".device_mac_rules\"$device_mac\".rules | to_entries[] | select(.key|match(\"bacnet\").value[]"
    packet_count=$(jq "$jq_filter" $rule_counts_file || true)
    echo device-$device_num $type $((packet_count > 2)) | tee -a $TEST_RESULTS
}

function terminate_processes {
    for process in daq ta; do
        pid=$(<inst/$process.pid)
        sudo kill -SIGINT $pid
        while [ -f inst/$process.pid ]; do
            echo Waiting for $process to exit...
            sleep 5
        done
    done
}

function test_mud {
    type=$1
    echo %%%%%%%%%%%%%%%%% test mud profile $type
    
    device_specs_file="resources/device_specs/bacnet_$type.json"
    rule_counts_file=inst/device_rule_counts.json

    cmd/run -k -s device_specs=$device_spces_file &
    $PYTHON_CMD daq/traffic_analyzer.py $device_specs_file $rule_counts_file &
    sleep 180

    echo result $type | tee -a $TEST_RESULTS

    test_device_traffic 1
    test_device_traffic 2

    test_acl_count 1
    test_acl_count 2

    more inst/run-*/nodes/*/activate.log | cat

    terminate_processes
}

activate_venv

test_mud open
test_mud todev
test_mud none
test_mud star

echo %%%%%%%%%%%%%%%%%%%%%% Done with tests | tee -a $TEST_RESULTS
