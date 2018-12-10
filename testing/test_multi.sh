#!/bin/bash

if [ `whoami` != 'root' ]; then
    echo Need to run as root.
    exit -1
fi

echo Writing test results to $TEST_RESULTS
cmdrun="cmd/run codecov"

cp misc/system_multi.conf local/system.conf

echo DAQ stress test | tee $TEST_RESULTS
$cmdrun -f run_limit=20
more inst/run-port-*/nodes/nmap*/return_code.txt | tee -a $TEST_RESULTS

echo Done with tests | tee -a $TEST_RESULTS
