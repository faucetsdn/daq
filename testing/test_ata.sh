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
    opts: telnet
    port: 2
  faux-8:
    opts: -n
    port: 8
EOF

cmd/run -s

fgrep RESULT inst/reports/report_9a02571e8f01_*.md | tee -a $TEST_RESULTS
fgrep RESULT inst/reports/report_9a02571e8f02_*.md | tee -a $TEST_RESULTS

echo Done with tests | tee -a $TEST_RESULTS
