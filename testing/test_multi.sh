#!/bin/bash

if [ `whoami` != 'root' ]; then
    echo Need to run as root.
    exit -1
fi

cp misc/system_multi.conf local/system.conf

echo DAQ stress test | tee -a $TEST_RESULTS
cmd/run -f run_limit=20
more inst/run-port-*/nodes/nmap*/return_code.txt | tee -a $TEST_RESULTS

echo Done with tests | tee -a $TEST_RESULTS
