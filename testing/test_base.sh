#!/bin/bash

source testing/test_preamble.sh

echo Base Tests >> $TEST_RESULTS

cp misc/system_base.conf local/system.conf

rm -rf inst/tmp_site && mkdir -p inst/tmp_site
cp misc/report_template.md inst/tmp_site/

echo Creating MUD templates...
bin/mudacl

echo %%%%%%%%%%%%%%%%%%%%%% Base tests | tee -a $TEST_RESULTS
cmd/run -b -s site_path=inst/tmp_site
more inst/result.log | tee -a $TEST_RESULTS

echo Redacted report for 9a02571e8f00:
cat inst/reports/report_9a02571e8f00_*.md | redact | tee -a $TEST_RESULTS

# Check that an open port causes the appropriate failure.
echo %%%%%%%%%%%%%%%%%%%%%% Telnet fail | tee -a $TEST_RESULTS
cmd/run -s startup_faux_opts=telnet
more inst/result.log | tee -a $TEST_RESULTS
cat inst/run-port-01/nodes/nmap01/activate.log
fgrep 'security.ports.nmap' inst/reports/report_9a02571e8f00_*.md | tee -a $TEST_RESULTS

# Except with a default MUD file that blocks the port.
echo %%%%%%%%%%%%%%%%%%%%%% Default MUD | tee -a $TEST_RESULTS
echo device_specs=misc/device_specs/simple.json >> local/system.conf
cmd/run -s startup_faux_opts=telnet
more inst/result.log | tee -a $TEST_RESULTS
fgrep 'security.ports.nmap'  inst/reports/report_9a02571e8f00_*.md | tee -a $TEST_RESULTS
cat inst/run-port-01/nodes/nmap01/activate.log

# Test an "external" switch.
echo %%%%%%%%%%%%%%%%%%%%%% External switch tests | tee -a $TEST_RESULTS
cp misc/system_ext.conf local/system.conf
cmd/run -s
more inst/result.log | tee -a $TEST_RESULTS
fgrep dp_id inst/faucet.yaml | tee -a $TEST_RESULTS
fgrep -i switch inst/run-port-02/nodes/ping02/activate.log | tee -a $TEST_RESULTS
more inst/run-port-02/nodes/ping02/activate.log | cat
count=$(fgrep icmp_seq=5 inst/run-port-02/nodes/ping02/activate.log | wc -l)
echo switch ping $count | tee -a $TEST_RESULTS

# Test various configurations of mud files.

echo %%%%%%%%%%%%%%%%%%%%%% Mud profile tests | tee -a $TEST_RESULTS
cp misc/system_muddy.conf local/system.conf

port_1_traffic="tcpdump -en -r inst/run-port-01/scans/monitor.pcap port 47808"
port_1_bcast_2="$port_1_traffic and ether src 9a:02:57:1e:8f:02 and ether broadcast"
port_1_ucast_2="$port_1_traffic and ether src 9a:02:57:1e:8f:02 and ether dst 9a:02:57:1e:8f:01"
port_1_bcast_3="$port_1_traffic and ether src 9a:02:57:1e:8f:03 and ether broadcast"
port_1_ucast_3="$port_1_traffic and ether src 9a:02:57:1e:8f:03 and ether dst 9a:02:57:1e:8f:01"
port_2__traffic="tcpdump -en -r inst/run-port-02/scans/monitor.pcap port 47808"
port_2_bcast_1="$port_2_traffic and ether src 9a:02:57:1e:8f:01 and ether broadcast"
port_2_ucast_1="$port_2_traffic and ether src 9a:02:57:1e:8f:01 and ether dst 9a:02:57:1e:8f:02"
port_2_bcast_3="$port_2_traffic and ether src 9a:02:57:1e:8f:03 and ether broadcast"
port_2_ucast_3="$port_2_traffic and ether src 9a:02:57:1e:8f:03 and ether dst 9a:02:57:1e:8f:02"

function test_mud {
    type=$1
    echo %%%%%%%%%%%%%%%%% test mud profile $type
    cmd/run -s device_specs=misc/device_specs/bacnet_$type.json
    echo result $type $(sort inst/result.log) | tee -a $TEST_RESULTS
    bcast_2=$($port_1_bcast_2 | wc -l)
    ucast_2=$($port_1_ucast_2 | wc -l)
    bcast_3=$($port_1_bcast_3 | wc -l)
    ucast_3=$($port_1_ucast_3 | wc -l)
    echo port_1 $type $(($bcast_2 > 0)) $(($ucast_2 > 0)) $(($bcast_3 > 0)) $(($ucast_3 > 0)) | tee -a $TEST_RESULTS
    bcast_1=$($port_2_bcast_1 | wc -l)
    ucast_1=$($port_2_ucast_1 | wc -l)
    bcast_3=$($port_2_bcast_3 | wc -l)
    ucast_3=$($port_2_ucast_3 | wc -l)
    echo port_2 $type $(($bcast_2 > 0)) $(($ucast_2 > 0)) $(($bcast_3 > 0)) $(($ucast_3 > 0)) | tee -a $TEST_RESULTS
    more inst/run-port-*/nodes/*/activate.log | cat
}

test_mud open
test_mud base
test_mud mix
test_mud none
test_mud star

echo %%%%%%%%%%%%%%%%%%%%%% Done with tests | tee -a $TEST_RESULTS
