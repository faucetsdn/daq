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
DAQ_FAUX1_OPTS=brute DAQ_FAUX2_OPTS=nobrute cmd/run -s
tail -qn 1 inst/run-port-*/nodes/brute*/tmp/report.txt | tee -a $TEST_RESULTS
sort inst/result.log | tee -a $TEST_RESULTS
more inst/run-port-*/nodes/ping*/activate.log
more inst/run-port-*/nodes/nmap*/activate.log
more inst/run-port-*/nodes/brute*/activate.log
ls inst/fail_fail01/ | tee -a $TEST_RESULTS

echo Done with tests | tee -a $TEST_RESULTS
