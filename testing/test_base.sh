#!/bin/bash

source testing/test_preamble.sh

echo Base Tests >> $TEST_RESULTS

rm -rf inst/tmp_site && mkdir -p inst/tmp_site
cp resources/setups/baseline/report_template.md inst/tmp_site/

echo Creating MUD templates...
bin/mudacl

bin/build_proto check || exit 1

echo %%%%%%%%%%%%%%%%%%%%%% Base tests | tee -a $TEST_RESULTS
rm -f local/system.yaml local/system.conf
# Check that bringing down the trunk interface terminates DAQ.
MARKER=inst/run-port-01/nodes/hold01/activate.log
monitor_marker $MARKER "sudo ip link set pri-eth1 down"
cmd/run -b -k -s site_path=inst/tmp_site
echo DAQ result code $? | tee -a $TEST_RESULTS
more inst/result.log | tee -a $TEST_RESULTS

echo Redacted report for 9a02571e8f00:
cat inst/reports/report_9a02571e8f00_*.md | redact | tee -a $TEST_RESULTS

# Check that an open port causes the appropriate failure.
echo %%%%%%%%%%%%%%%%%%%%%% Telnet fail | tee -a $TEST_RESULTS
docker rmi daqf/test_hold:latest # Check case of missing image
cmd/run -s -k interfaces.faux.opts=telnet
echo DAQ result code $? | tee -a $TEST_RESULTS
more inst/result.log | tee -a $TEST_RESULTS
cat inst/run-port-01/nodes/nmap01/activate.log
fgrep 'security.ports.nmap' inst/reports/report_9a02571e8f00_*.md | tee -a $TEST_RESULTS
DAQ_TARGETS=test_hold cmd/build

# Except with a default MUD file that blocks the port.
echo %%%%%%%%%%%%%%%%%%%%%% Default MUD | tee -a $TEST_RESULTS
cmd/run -s interfaces.faux.opts=telnet device_specs=resources/device_specs/simple.json
echo DAQ result code $? | tee -a $TEST_RESULTS
more inst/result.log | tee -a $TEST_RESULTS
fgrep 'security.ports.nmap'  inst/reports/report_9a02571e8f00_*.md | tee -a $TEST_RESULTS
cat inst/run-port-01/nodes/nmap01/activate.log

echo %%%%%%%%%%%%%%%%%%%%%% External switch tests | tee -a $TEST_RESULTS
cp config/system/ext.yaml local/system.yaml
cmd/run -s
cat inst/result.log | tee -a $TEST_RESULTS
fgrep dp_id inst/faucet.yaml | tee -a $TEST_RESULTS
fgrep -i switch inst/run-port-02/nodes/ping02/activate.log | tee -a $TEST_RESULTS
cat -vet inst/run-port-02/nodes/ping02/activate.log
count=$(fgrep icmp_seq=5 inst/run-port-02/nodes/ping02/activate.log | wc -l)
echo switch ping $count | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%% Mud profile tests | tee -a $TEST_RESULTS
rm -f local/system.yaml
cp config/system/muddy.conf local/system.conf

device_traffic="tcpdump -en -r inst/run-port-01/scans/monitor.pcap port 47808"
device_bcast="$device_traffic and ether broadcast"
device_ucast="$device_traffic and ether dst 9a:02:57:1e:8f:02"
device_xcast="$device_traffic and ether dst 9a:02:57:1e:8f:03"
cntrlr_traffic="tcpdump -en -r inst/run-port-02/scans/monitor.pcap port 47808"
cntrlr_bcast="$cntrlr_traffic and ether broadcast"
cntrlr_ucast="$cntrlr_traffic and ether dst 9a:02:57:1e:8f:01"
cntrlr_xcast="$cntrlr_traffic and ether dst 9a:02:57:1e:8f:03"

function test_mud {
    type=$1
    echo %%%%%%%%%%%%%%%%% test mud profile $type
    cmd/run -s device_specs=resources/device_specs/bacnet_$type.json
    echo result $type $(sort inst/result.log) | tee -a $TEST_RESULTS
    bcast=$($device_bcast | wc -l)
    ucast=$($device_ucast | wc -l)
    xcast=$($device_xcast | wc -l)
    echo device $type $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS
    bcast=$($cntrlr_bcast | wc -l)
    ucast=$($cntrlr_ucast | wc -l)
    xcast=$($cntrlr_xcast | wc -l)
    echo cntrlr $type $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS
    more inst/run-port-*/nodes/*/activate.log | cat
}

test_mud open
test_mud base
test_mud todev
test_mud frdev
test_mud none
test_mud star

echo %%%%%%%%%%%%%%%%%%%%%% Done with tests | tee -a $TEST_RESULTS
