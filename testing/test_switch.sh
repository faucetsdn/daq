#!/bin/bash

source testing/test_preamble.sh

echo Switch Tests >> $TEST_RESULTS

rm -rf inst/tmp_site && mkdir -p inst/tmp_site
cp resources/setups/baseline/report_template.md inst/tmp_site/

if [ -d venv ]; then
    echo Activating venv
    source venv/bin/activate
fi

echo Installing faucet...
pip3 --no-cache-dir install --upgrade faucet/
cp faucet/etc/faucet/ryu.conf inst/

echo Creating MUD templates...
bin/mudacl

build_if_not_release

# Tests the case where there is an external switch, controlled by DAQ.
# Specifically, the startup sequence starts an OVS instance outside of
# DAQ to simulate the existence of an external switch. This is
# triggered by the switch_setup.ext_br property being set (external OVS).
echo %%%%%%%%%%%%%%%%%%%%%% External switch tests | tee -a $TEST_RESULTS
echo 'include: ../config/system/ext.yaml' > local/system.yaml
cmd/run -s
cat inst/result.log | tee -a $TEST_RESULTS
fgrep dp_id inst/faucet.yaml | tee -a $TEST_RESULTS
fgrep -i switch inst/run-9a02571e8f00/nodes/ping*/activate.log | fgrep -v test_ | sed -e "s/\r//g" | tee -a $TEST_RESULTS
cat -vet inst/run-9a02571e8f00/nodes/ping*/activate.log
count=$(fgrep icmp_seq=5 inst/run-9a02571e8f00/nodes/ping*/activate.log | wc -l)
echo switch ping $count | tee -a $TEST_RESULTS

# Tests the use of an 'alternate' switch stack, which exists outside of
# DAQ. This includes both the switch and controller existing exteranlly.
# This is triggered by both switch_setup.ext_br (external OVS), and
# switch_setup.alt_of_port (external faucet) configuration parameters.
echo %%%%%%%%%%%%%%%%%%%%%% Alt switch tests | tee -a $TEST_RESULTS
echo 'include: ../config/system/alt.yaml' > local/system.yaml

timeout 1200s cmd/run -s

# Make sure it started faucet in native mode.
fgrep "Started faucet pid" inst/cmdrun.log

fgrep 'Learning 9a:02:57:1e:8f:01 on vid 1002' inst/cmdrun.log | head -1 | redact | tee -a $TEST_RESULTS
unique_ips=$(fgrep '10.20.99' inst/run-9a02571e8f01/scans/ip_triggers.txt | awk '{print $1}' | sort | uniq | wc -l)
echo 9a:02:57:1e:8f:01 Unique IPs: $unique_ips | tee -a $TEST_RESULTS
fgrep 'RESULT ' inst/run-9a02571e8f01/nodes/ping*/activate.log | tee -a $TEST_RESULTS

unique_ips=$(fgrep '10.20.1' inst/run-9a02571e8f02/scans/ip_triggers.txt | awk '{print $1}' | sort | uniq | wc -l)
echo 9a:02:57:1e:8f:02 Unique IPs: $unique_ips | tee -a $TEST_RESULTS

more inst/run-*/scans/ip_triggers.txt | cat

# acquire test will fail since the DHCP server never even tries
fgrep 9a02571e8f03 inst/result.log | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%% Native gauge test | tee -a $TEST_RESULTS

cmd/faucet native gauge
ps ax | fgrep faucet.gauge | fgrep $(< inst/gauge.pid)
fgrep "watching FAUCET config" inst/gauge.log

cmd/faucet native kill gauge
[ ! -f inst/gauge.pid ]

echo %%%%%%%%%%%%%%%%%%%%%% Done with tests | tee -a $TEST_RESULTS
