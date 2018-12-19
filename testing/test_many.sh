#!/bin/bash

if [ `whoami` != 'root' ]; then
    echo Need to run as root.
    exit -1
fi

echo Writing test results to $TEST_RESULTS
cmdrun="cmd/run codecov"

echo source misc/system.conf > local/system.conf

manystartup=inst/startup_many.cmd
rm -f $manystartup
echo startup_cmds=$manystartup >> local/system.conf

echo sec_port=10 >> local/system.conf

ifaces=
for iface in 1 2 3 4 5 6 7 8 9; do
    ifaces=${ifaces},faux-$iface
    echo autostart cmd/faux $iface >> $manystartup
done
echo intf_names=${ifaces#,} >> local/system.conf


echo DAQ stress test | tee $TEST_RESULTS
$cmdrun -f run_limit=50
more inst/run-port-*/nodes/nmap*/return_code.txt | tee -a $TEST_RESULTS

echo Done with tests | tee -a $TEST_RESULTS
