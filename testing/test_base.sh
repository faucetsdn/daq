#!/bin/bash

source testing/test_preamble.sh

echo Base Tests >> $TEST_RESULTS

rm -rf inst/tmp_site && mkdir -p inst/tmp_site
cp resources/setups/baseline/report_template.md inst/tmp_site/
cp resources/test_site/site_config.json inst/tmp_site/site_config.json
cat <<EOF > inst/tmp_site/site_config.json
    {
        "modules": {
            "discover": {
                "enabled": false
            },
             "bacnet": {
                "enabled": false
            },
             "mudgee": {
                "enabled": false
            }
        }
    }
EOF

echo Creating MUD templates...
bin/mudacl

bin/build_proto check || exit 1

echo %%%%%%%%%%%%%%%%%%%%%% Base tests | tee -a $TEST_RESULTS
rm -f local/system.yaml local/system.conf
# Check that bringing down the trunk interface terminates DAQ.
MARKER=inst/run-9a02571e8f00/nodes/hold*/activate.log
monitor_marker $MARKER "sudo ip link set pri-eth1 down"
cmd/run -b -k -s site_path=inst/tmp_site
echo DAQ result code $? | tee -a $TEST_RESULTS
cat inst/result.log | tee -a $TEST_RESULTS

echo Redacted report for 9a02571e8f00:
cat inst/reports/report_9a02571e8f00_*.md | redact | tee -a $TEST_RESULTS

# Check that an open port causes the appropriate failure.
echo %%%%%%%%%%%%%%%%%%%%%% Telnet fail | tee -a $TEST_RESULTS
docker rmi daqf/test_hold:latest # Check case of missing image
cmd/run -s -k interfaces.faux.opts=telnet
echo DAQ result code $? | tee -a $TEST_RESULTS
cat inst/result.log | tee -a $TEST_RESULTS
cat inst/run-9a02571e8f00/nodes/nmap01/activate.log
fgrep 'security.nmap.ports' inst/reports/report_9a02571e8f00_*.md | tee -a $TEST_RESULTS
DAQ_TARGETS=test_hold cmd/build

# Except with a default MUD file that blocks the port.
echo %%%%%%%%%%%%%%%%%%%%%% Default MUD | tee -a $TEST_RESULTS
cmd/run -s interfaces.faux.opts=telnet device_specs=resources/device_specs/simple.json
echo DAQ result code $? | tee -a $TEST_RESULTS
cat inst/result.log | tee -a $TEST_RESULTS
fgrep 'security.nmap.ports'  inst/reports/report_9a02571e8f00_*.md | tee -a $TEST_RESULTS
cat inst/run-9a02571e8f00/nodes/nmap01/activate.log

echo %%%%%%%%%%%%%%%%%%%%%% External switch tests | tee -a $TEST_RESULTS
echo 'include: ../config/system/ext.yaml' > local/system.yaml
cmd/run -s
cat inst/result.log | tee -a $TEST_RESULTS
fgrep dp_id inst/faucet.yaml | tee -a $TEST_RESULTS
fgrep -i switch inst/run-9a02571e8f00/nodes/ping*/activate.log | sed -e "s/\r//g" | tee -a $TEST_RESULTS
cat -vet inst/run-9a02571e8f00/nodes/ping*/activate.log
count=$(fgrep icmp_seq=5 inst/run-9a02571e8f00/nodes/ping*/activate.log | wc -l)
echo switch ping $count | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%% Alt switch tests | tee -a $TEST_RESULTS
echo 'include: ../config/system/alt.yaml' > local/system.yaml
cmd/faucet

timeout 1200s cmd/run -s

fgrep 'Learned 9a:02:57:1e:8f:01 on vid 1002' inst/cmdrun.log | head -1 | redact | tee -a $TEST_RESULTS
unqie_ips=$(fgrep '10.20.99' inst/run-9a02571e8f01/scans/ip_triggers.txt | awk '{print $1}' | sort | uniq | wc -l)
echo Unique IPs: $unqie_ips | tee -a $TEST_RESULTS

fgrep RESULT inst/run-9a02571e8f01/nodes/ping01/activate.log | tee -a $TEST_RESULTS

# acquire test will fail since the DHCP server never even tries
fgrep 9a02571e8f02 inst/result.log | tee -a $TEST_RESULTS

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
