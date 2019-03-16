#!/bin/bash

source testing/test_preamble.sh

echo Aux Tests >> $TEST_RESULTS

echo mudacl tests | tee -a $TEST_RESULTS
mudacl/bin/test.sh
echo Mudacl exit code $? | tee -a $TEST_RESULTS
validator/bin/test.sh
echo Validator exit code $? | tee -a $TEST_RESULTS

# Runs lint checks and some similar things
echo Lint checks | tee -a $TEST_RESULTS
cmd/inbuild skip
echo cmd/inbuild exit code $? | tee -a $TEST_RESULTS

echo Extended tests | tee -a $TEST_RESULTS
cp misc/system_multi.conf local/system.conf
echo fail_hook=misc/dump_network.sh >> local/system.conf
echo test_config=misc/runtime_configs/long_wait >> local/system.conf
DAQ_FAUX1_OPTS=brute DAQ_FAUX2_OPTS=nobrute cmd/run -s site_path=misc/test_site
tail -qn 1 inst/run-port-*/nodes/brute*/tmp/report.txt | tee -a $TEST_RESULTS
more inst/run-port-*/scans/dhcp_triggers.txt | cat
dhcp_short=$(fgrep None inst/run-port-01/scans/dhcp_triggers.txt | wc -l)
dhcp_long=$(fgrep long inst/run-port-01/scans/dhcp_triggers.txt | wc -l)
echo dhcp requests $dhcp_short $dhcp_long | tee -a $TEST_RESULTS
sort inst/result.log | tee -a $TEST_RESULTS
more inst/run-port-*/nodes/ping*/activate.log | cat
more inst/run-port-*/nodes/nmap*/activate.log | cat
more inst/run-port-*/nodes/brute*/activate.log | cat
ls inst/fail_fail01/ | tee -a $TEST_RESULTS

echo @@@@@@@ Sample report with template device description
cat inst/reports/report_9a02571e8f01_*.txt
echo @@@@@@@ Done with sample report.

echo Done with tests | tee -a $TEST_RESULTS
