#!/bin/bash

source testing/test_preamble.sh

echo Base Tests >> $TEST_RESULTS

function redact {
    sed -E -e 's/\s*%%.*//' \
        -e 's/[0-9]{4}-.*T.*Z/XXX/' \
        -e 's/[0-9]{4}-(0|1)[0-9]-(0|1|2|3)[0-9] [0-9]{2}:[0-9]{2}:[0-9]{2}\+00:00/XXX/g' \
        -e 's/DAQ version.*//'
}

cp misc/system_base.conf local/system.conf

rm -rf inst/tmp_site && mkdir -p inst/tmp_site
cp misc/report_template.md inst/tmp_site/

cmd/run -s site_path=inst/tmp_site
more inst/result.log | tee -a $TEST_RESULTS
cat inst/reports/report_9a02571e8f00_*.md | redact | tee -a $TEST_RESULTS

# Test block for open-port failures.
echo Open port tests | tee -a $TEST_RESULTS

# Check that an open port causes the appropriate failure.
cmd/run -s startup_faux_opts=telnet
more inst/result.log | tee -a $TEST_RESULTS
cat inst/run-port-01/nodes/nmap01/activate.log
fgrep 'security.ports.nmap' inst/reports/report_9a02571e8f00_*.md | tee -a $TEST_RESULTS

# Except with a default MUD file that blocks the port.
echo device_specs=misc/device_specs/simple.json >> local/system.conf
cmd/run -s startup_faux_opts=telnet
more inst/result.log | tee -a $TEST_RESULTS
fgrep 'security.ports.nmap'  inst/reports/report_9a02571e8f00_*.md | tee -a $TEST_RESULTS
cat inst/run-port-01/nodes/nmap01/activate.log

# Test an "external" switch.
echo External switch tests | tee -a $TEST_RESULTS
cp misc/system_ext.conf local/system.conf
cmd/run -s
more inst/result.log | tee -a $TEST_RESULTS
fgrep dp_id inst/faucet.yaml | tee -a $TEST_RESULTS
fgrep -i switch inst/run-port-02/nodes/ping02/activate.log | tee -a $TEST_RESULTS
count=$(fgrep icmp_seq=5 inst/run-port-02/nodes/ping02/activate.log | wc -l)
echo switch ping $count | tee -a $TEST_RESULTS
ls -l inst/gw*/nodes/gw*/tmp/startup.pcap

# Test various configurations of mud files.

echo Mud profile tests | tee -a $TEST_RESULTS
cp misc/system_muddy.conf local/system.conf

device_traffic="tcpdump -en -r inst/run-port-01/scans/monitor.pcap port 47808"
device_bcast="$device_traffic and ether broadcast"
device_ucast="$device_traffic and ether dst 9a:02:57:1e:8f:02"
device_xcast="$device_traffic and ether host 9a:02:57:1e:8f:03"
cntrlr_traffic="tcpdump -en -r inst/run-port-02/scans/monitor.pcap port 47808"
cntrlr_bcast="$cntrlr_traffic and ether broadcast"
cntrlr_ucast="$cntrlr_traffic and ether dst 9a:02:57:1e:8f:01"
cntrlr_xcast="$cntrlr_traffic and ether host 9a:02:57:1e:8f:03"

function test_mud {
    type=$1
    cmd/run -s device_specs=misc/device_specs/bacnet_$type.json
    echo result $type $(sort inst/result.log) | tee -a $TEST_RESULTS
    bcast=$($device_bcast | wc -l)
    ucast=$($device_ucast | wc -l)
    xcast=$($device_xcast | wc -l)
    echo device $type $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS
    bcast=$($cntrlr_bcast | wc -l)
    ucast=$($cntrlr_ucast | wc -l)
    xcast=$($cntrlr_xcast | wc -l)
    echo cntrlr $type $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS
}

test_mud open
test_mud base
test_mud todev
test_mud frdev
test_mud none
test_mud star

echo Done with tests | tee -a $TEST_RESULTS
