#!/bin/bash

if [ `whoami` != 'root' ]; then
    echo Need to run as root.
    exit -1
fi

cp misc/system_base.conf local/system.conf

cmd/run codecov -s
echo Base tests | tee -a $TEST_RESULTS
more inst/result.log | tee -a $TEST_RESULTS

# Test block for open-port failures.
(
    echo Open port tests | tee -a $TEST_RESULTS

    export DAQ_FAUX_OPTS=telnet
    # Check that an open port causes the appropriate failure.
    cmd/run -s
    more inst/result.log | tee -a $TEST_RESULTS
    cat inst/run-port-01/nodes/nmap01/activate.log

    # Except with a default MUD file that blocks the port.
    echo device_specs=misc/device_specs.json >> local/system.conf
    cmd/run -s
    more inst/result.log | tee -a $TEST_RESULTS
    cat inst/run-port-01/nodes/nmap01/activate.log
)

# Test an "external" switch.
echo External switch tests | tee -a $TEST_RESULTS
cp misc/system_ext.conf local/system.conf
cmd/run -s
more inst/result.log | tee -a $TEST_RESULTS
fgrep dp_id inst/faucet.yaml | tee -a $TEST_RESULTS

# Test various configurations of mud files.

echo Mud profile tests | tee -a $TEST_RESULTS
cp misc/system_multi.conf local/system.conf
echo add ping > inst/ping_only.conf
echo host_tests=inst/ping_only.conf >> local/system.conf

bin/mudacl
bacnet_traffic="tcpdump -en -r inst/run-port-01/scans/monitor.pcap port 47808"
bacnet_bcast="$bacnet_traffic and ether broadcast"
bacnet_ucast="$bacnet_traffic and ether src 9a:02:57:1e:8f:01 and ether dst 9a:02:57:1e:8f:02"

export DAQ_FAUX1_OPTS=bacnet
export DAQ_FAUX2_OPTS=discover
export DAQ_FAUX3_OPTS=discover

cmd/run -s device_specs=misc/device_specs_bacnet.json
bcast=$($bacnet_bcast | wc -l)
ucast=$($bacnet_ucast | wc -l)
echo bacnet base discovery $(($bcast > 2)) and $(($ucast > 2)) | tee -a $TEST_RESULTS

cmd/run -s device_specs=misc/device_specs_bacnet_todev.json
bcast=$($bacnet_bcast | wc -l)
ucast=$($bacnet_ucast | wc -l)
echo bacnet todev $(($bcast > 2)) and $(($ucast > 2)) | tee -a $TEST_RESULTS

cmd/run -s device_specs=misc/device_specs_bacnet_frdev.json
bcast=$($bacnet_bcast | wc -l)
ucast=$($bacnet_ucast | wc -l)
echo bacnet frdev $(($bcast > 2)) and $(($ucast > 2)) | tee -a $TEST_RESULTS

cmd/run -s device_specs=misc/device_specs_bacnet_disabled.json
bcast=$($bacnet_bcast | wc -l)
ucast=$($bacnet_ucast | wc -l)
echo bacnet none $(($bcast > 2)) and $(($ucast > 2)) | tee -a $TEST_RESULTS

unset DAQ_FAUX1_OPTS
unset DAQ_FAUX2_OPTS
unset DAQ_FAUX3_OPTS

echo Done with tests | tee -a $TEST_RESULTS
