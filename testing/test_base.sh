#!/bin/bash

source testing/test_preamble.sh

echo Base Tests >> $TEST_RESULTS

rm -rf inst/tmp_site && mkdir -p inst/tmp_site
cp resources/setups/baseline/report_template.md inst/tmp_site/

echo Creating MUD templates...
bin/mudacl

bin/build_proto check || exit 1

echo %%%%%%%%%%%%%%%%%%%%%% Base tests | tee -a $TEST_RESULTS
# Check that bringing down the trunk interface terminates DAQ.
rm -f local/system.yaml local/system.conf
MARKER=inst/run-9a02571e8f00/nodes/hold*/activate.log
monitor_marker $MARKER "sudo ip link set pri-eth1 down"
cmd/run -b -k -s site_path=inst/tmp_site
echo DAQ result code $? | tee -a $TEST_RESULTS
cat inst/result.log | tee -a $TEST_RESULTS

echo Redacted report for 9a02571e8f00:
cat inst/reports/report_9a02571e8f00_*.md | redact | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%% Report Finalizing Exception handling | tee -a $TEST_RESULTS
# Check exception handling during report finalizing.
mv resources/setups/baseline/device_report.css resources/setups/baseline/device_report
cmd/run -s
mv resources/setups/baseline/device_report resources/setups/baseline/device_report.css
cat inst/result.log | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%% Telnet fail | tee -a $TEST_RESULTS
# Check that an open port causes the appropriate failure.
docker rmi daqf/test_hold:latest # Check case of missing image
cmd/run -s -k interfaces.faux.opts=telnet
echo DAQ result code $? | tee -a $TEST_RESULTS
cat inst/result.log | tee -a $TEST_RESULTS
cat inst/run-9a02571e8f00/nodes/nmap01/activate.log
fgrep 'security.nmap.ports' inst/reports/report_9a02571e8f00_*.md | tee -a $TEST_RESULTS
DAQ_TARGETS=test_hold cmd/build

echo %%%%%%%%%%%%%%%%%%%%%% Done with tests | tee -a $TEST_RESULTS
