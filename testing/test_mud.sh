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
echo 'include=../config/system/muddy.conf' > local/system.conf

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
    peer_num=$((3-device_num))
    device_mac=9a:02:57:1e:8f:0$device_num
    peer_mac=9a:02:57:1e:8f:0$peer_num
    metric_output_file=inst/run-9a02571e8f0$device_num/metric_output.json
    rule_filter=eth_src=$peer_mac,eth_dst=$device_mac

    echo DAQ_CODECOV: $DAQ_CODECOV
    python3 daq/varz_state_collector.py -y flow_packet_count_port_acl -o $metric_output_file -l $rule_filter
    packet_count=$(jq '.gauge_metrics.flow_packet_count_port_acl.samples[0].value' $metric_output_file)
    echo device-$device_num $type $((packet_count > 2)) | tee -a $TEST_RESULTS
}

function terminate_daq {
    daq_pid=$(<inst/daq.pid)
    sudo kill -SIGINT $daq_pid
    while [ -f inst/daq.pid ]; do
        echo Waiting for DAQ to exit...
        sleep 5
    done
}

function test_mud {
    type=$1
    echo %%%%%%%%%%%%%%%%% test mud profile $type
    cmd/run -k -s device_specs=resources/device_specs/bacnet_$type.json &
    sleep 120

    echo result $type | tee -a $TEST_RESULTS

    test_device_traffic 1
    test_device_traffic 2

    test_acl_count 1
    test_acl_count 2

    more inst/run-*/nodes/*/activate.log | cat

    terminate_daq
}

test_mud open
test_mud todev
test_mud none
test_mud star

echo %%%%%%%%%%%%%%%%%%%%%% Done with tests | tee -a $TEST_RESULTS
