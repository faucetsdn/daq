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
echo add ping > inst/ping_only.conf

cp misc/system_multi.conf local/system.conf
echo host_tests=inst/ping_only.conf >> local/system.conf
echo startup_cmds=misc/startup_discover.cmd >> local/system.conf

bin/mudacl
device_traffic="tcpdump -en -r inst/run-port-01/scans/monitor.pcap port 47808"
device_bcast="$device_traffic and ether broadcast"
device_ucast="$device_traffic and ether dst 9a:02:57:1e:8f:02"
device_xcast="$device_traffic and ether dst 9a:02:57:1e:8f:03 or ether src 9a:02:57:1e:8f:03"
cntrlr_traffic="tcpdump -en -r inst/run-port-02/scans/monitor.pcap port 47808"
cntrlr_bcast="$cntrlr_traffic and ether broadcast"
cntrlr_ucast="$cntrlr_traffic and ether dst 9a:02:57:1e:8f:01"
cntrlr_xcast="$cntrlr_traffic and ether dst 9a:02:57:1e:8f:03 or ether src 9a:02:57:1e:8f:03"

$cmdrun -s
bcast=$($device_bcast | wc -l)
ucast=$($device_ucast | wc -l)
xcast=$($device_xcast | wc -l)
echo device open $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS
bcast=$($cntrlr_bcast | wc -l)
ucast=$($cntrlr_ucast | wc -l)
xcast=$($cntrlr_xcast | wc -l)
echo cntrlr open $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS

$cmdrun -s device_specs=misc/device_specs_bacnet.json
bcast=$($device_bcast | wc -l)
ucast=$($device_ucast | wc -l)
xcast=$($device_xcast | wc -l)
echo device base $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS
bcast=$($cntrlr_bcast | wc -l)
ucast=$($cntrlr_ucast | wc -l)
xcast=$($cntrlr_xcast | wc -l)
echo cntrlr base $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS

$cmdrun -s device_specs=misc/device_specs_bacnet_todev.json
bcast=$($device_bcast | wc -l)
ucast=$($device_ucast | wc -l)
xcast=$($device_xcast | wc -l)
echo device todev $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS
bcast=$($cntrlr_bcast | wc -l)
ucast=$($cntrlr_ucast | wc -l)
xcast=$($cntrlr_xcast | wc -l)
echo cntrlr todev $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS

$cmdrun -s device_specs=misc/device_specs_bacnet_frdev.json
bcast=$($device_bcast | wc -l)
ucast=$($device_ucast | wc -l)
xcast=$($device_xcast | wc -l)
echo device frdev $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS
bcast=$($cntrlr_bcast | wc -l)
ucast=$($cntrlr_ucast | wc -l)
xcast=$($cntrlr_xcast | wc -l)
echo cntrlr frdev $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS

$cmdrun -s device_specs=misc/device_specs_bacnet_disabled.json
bcast=$($device_bcast | wc -l)
ucast=$($device_ucast | wc -l)
xcast=$($device_xcast | wc -l)
echo device none $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0))  | tee -a $TEST_RESULTS
bcast=$($cntrlr_bcast | wc -l)
ucast=$($cntrlr_ucast | wc -l)
xcast=$($cntrlr_xcast | wc -l)
echo cntrlr none $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0))  | tee -a $TEST_RESULTS

echo Done with tests | tee -a $TEST_RESULTS
