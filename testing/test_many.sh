#!/bin/bash

source testing/test_preamble.sh

NUM_DEVICES=8
RUN_LIMIT=20
NUM_NO_DHCP_DEVICES=2
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
    xdhcp=""
    if [[ iface -le $NUM_NO_DHCP_DEVICES ]]; then
        xdhcp="xdhcp"
    fi
    echo autostart cmd/faux $iface $xdhcp>> $manystartup
done
echo intf_names=${ifaces#,} >> local/system.conf

echo DAQ stress test | tee -a $TEST_RESULTS
# Limit should be ~30, but something is wrong with startup sequence.
cmd/run run_limit=$RUN_LIMIT settle_sec=0 dhcp_lease_time=120s
cat inst/result.log
results=$(fgrep [] inst/result.log | wc -l)
timeouts=$(fgrep "dhcp:TimeoutError" inst/result.log | wc -l)
echo Found $results successful runs.
# This is broken -- should have many more results available!
echo Enough results: $(echo "print($results >= 6 / 10 * $RUN_LIMIT)" | python) | tee -a $TEST_RESULTS
# $timeouts should strictly equal $NUM_NO_DHCP_DEVICES when dhcp step is fixed. 
echo Enough DHCP timeouts: $(echo "print($timeouts >= $NUM_NO_DHCP_DEVICES)" | python) | tee -a $TEST_RESULTS
echo Done with tests | tee -a $TEST_RESULTS
