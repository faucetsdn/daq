#!/bin/bash

source testing/test_preamble.sh

NUM_DEVICES=10

echo Many Tests >> $TEST_RESULTS

echo source misc/system.conf > local/system.conf

manystartup=inst/startup_many.cmd
rm -f $manystartup
echo startup_cmds=$manystartup >> local/system.conf

echo monitor_scan_sec=5 >> local/system.conf
echo sec_port=$((NUM_DEVICES+1)) >> local/system.conf

ifaces=
for iface in $(seq 1 $NUM_DEVICES); do
    ifaces=${ifaces},faux-$iface
    echo autostart cmd/faux $iface >> $manystartup
done
echo intf_names=${ifaces#,} >> local/system.conf

echo DAQ stress test | tee -a $TEST_RESULTS
cmd/run run_limit=40 settle_sec=0
cat inst/result.log
results=$(fgrep [] inst/result.log | wc -l)
echo Found $results successful runs.
echo Enough results $(($results >= 40)) | tee -a $TEST_RESULTS

echo Done with tests | tee -a $TEST_RESULTS
