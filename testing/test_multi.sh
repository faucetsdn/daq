#!/bin/bash

cp misc/system_multi.conf local/system.conf

cmd/run -f run_limit=20
more inst/run-port-*/nodes/nmap*/return_code.txt | tee -a $TEST_RESULTS
