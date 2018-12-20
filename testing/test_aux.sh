#!/bin/bash

if [ `whoami` != 'root' ]; then
    echo Need to run as root.
    exit -1
fi

echo DAQ aux tests | tee $TEST_RESULTS

mudacl/bin/test.sh
echo Mudacl exit code $? | tee -a $TEST_RESULTS
validator/bin/test.sh
echo Validator exit code $? | tee -a $TEST_RESULTS

# Runs lint checks and some similar things
cmd/inbuild skip
echo cmd/inbuild exit code $? | tee -a $TEST_RESULTS

echo Extended tests | tee -a $TEST_RESULTS
cp misc/system_multi.conf local/system.conf
export DAQ_FAUX1_OPTS=brute
export DAQ_FAUX2_OPTS=nobrute
cmd/run -s
more inst/run-port-*/nodes/brute*/tmp/report.txt
tail -qn 1 inst/run-port-*/nodes/brute*/tmp/report.txt | tee -a $TEST_RESULTS

echo Done with tests | tee -a $TEST_RESULTS
