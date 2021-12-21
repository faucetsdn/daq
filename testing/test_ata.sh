#!/bin/bash

source testing/test_preamble.sh

echo ATA Tests >> $TEST_RESULTS

cat <<EOF > local/system.yaml
include: ${DAQ_LIB}/config/system/ata.yaml
switch_setup:
  alt_of_port: 6669
  alt_varz_port: 9305
  ext_br: ata
interfaces:
  faux-1:
    opts: xdhcp 
    port: 1
  faux-2:
    opts: oddservices telnet snmp
    port: 2
  faux-3:
    opts: curl telnet
    port: 3
  faux-4:
    opts: ssh
    port: 4
  faux-8:
    opts: -n
    port: 8
EOF

# Not strictly necessary for test, but useful when running manually.
rm -rf inst/run-*

cmd/run -s

echo Looking for lack of queing activate...
! egrep 'Target device 9a02571e8f0. queing activate' inst/cmdrun.log

cat <<EOF >> local/system.yaml
run_trigger:
  max_hosts: 2
EOF

# Remove run dirs except one to properly check device_block_sec
rm -rf inst/reports inst/run-9a02571e8f01/ inst/run-9a02571e8f02/ inst/run-9a02571e8f04/

cmd/run -s

echo Looking for lack of queing activate...
egrep 'Target device 9a02571e8f0. queing activate \(2\)' inst/cmdrun.log

fgrep RESULT inst/reports/report_9a02571e8f01_*.md | tee -a $TEST_RESULTS
fgrep RESULT inst/reports/report_9a02571e8f02_*.md | tee -a $TEST_RESULTS
fgrep RESULT inst/reports/report_9a02571e8f03_*.md | tee -a $TEST_RESULTS
fgrep RESULT inst/reports/report_9a02571e8f04_*.md | tee -a $TEST_RESULTS

echo Done with tests | tee -a $TEST_RESULTS
