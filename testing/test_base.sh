#!/bin/bash

cp misc/system_base.conf local/system.conf

cmd/run codecov -s
more inst/result.log | tee -a $TEST_RESULTS

# Test block for open-port failures.
(
    echo Open port tests | tee -a $TEST_RESULTS

    export DAQ_FAUX_OPTS=telnet
    # Check that an open port causes the appropriate failure.
    cmd/run -s
    more inst/result.log | tee -a $TEST_RESULTS

    # Except with a default MUD file that blocks the port.
    echo device_specs=misc/device_specs.json >> local/system.conf
    cmd/run -s
    more inst/result.log | tee -a $TEST_RESULTS
)

# Test an "external" switch.
echo External switch tests | tee -a $TEST_RESULTS
cp misc/system_ext.conf local/system.conf
cmd/run codecov -s
more inst/result.log | tee -a $TEST_RESULTS
fgrep dp_id inst/faucet.yaml | tee -a $TEST_RESULTS
