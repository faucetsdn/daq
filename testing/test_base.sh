#!/bin/bash

if [ `whoami` != 'root' ]; then
    echo Need to run as root.
    exit -1
fi

echo Writing test results to $TEST_RESULTS
cmdrun="cmd/run codecov"

cp misc/system_base.conf local/system.conf

echo Base tests | tee $TEST_RESULTS
$cmdrun -s
more inst/result.log | tee -a $TEST_RESULTS

# Test block for open-port failures.
(
    echo Open port tests | tee -a $TEST_RESULTS

    export DAQ_FAUX_OPTS=telnet
    # Check that an open port causes the appropriate failure.
    $cmdrun -s
    more inst/result.log | tee -a $TEST_RESULTS
    cat inst/run-port-01/nodes/nmap01/activate.log

    # Except with a default MUD file that blocks the port.
    echo device_specs=misc/device_specs.json >> local/system.conf
    $cmdrun -s
    more inst/result.log | tee -a $TEST_RESULTS
    cat inst/run-port-01/nodes/nmap01/activate.log
)

# Test an "external" switch.
echo External switch tests | tee -a $TEST_RESULTS
cp misc/system_ext.conf local/system.conf
$cmdrun -s
more inst/result.log | tee -a $TEST_RESULTS
fgrep dp_id inst/faucet.yaml | tee -a $TEST_RESULTS
fgrep time inst/run-port-02/nodes/ping02/activate.log
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
    $cmdrun -s device_specs=misc/device_specs_bacnet_$type.json
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
