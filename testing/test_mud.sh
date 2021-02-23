#!/bin/bash

source testing/test_preamble.sh

echo MUD Tests >> $TEST_RESULTS

echo Creating MUD templates...
bin/mudacl

release_tag=`git describe --dirty || echo unknown`
build_mode=
# If the current commit is a release tag, then pull images.
echo Processing release tag $release_tag
if [[ "$release_tag" != unknown && ! "$release_tag" =~ -.*- ]]; then
    build_mode=pull
fi
cmd/build $build_mode build

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

function test_mud {
    type=$1
    echo %%%%%%%%%%%%%%%%% test mud profile $type
    cmd/run -s device_specs=resources/device_specs/bacnet_$type.json

    echo result $type $(sort inst/result.log) | tee -a $TEST_RESULTS

    test_device_traffic 1
    test_device_traffic 2

    more inst/run-*/nodes/*/activate.log | cat
}

test_mud open
test_mud todev
test_mud none
test_mud star

echo %%%%%%%%%%%%%%%%%%%%%% Done with tests | tee -a $TEST_RESULTS
