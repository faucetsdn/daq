#!/bin/bash

source testing/test_preamble.sh

echo Aux Tests >> $TEST_RESULTS

echo mudacl tests | tee -a $TEST_RESULTS
mudacl/bin/test.sh
echo Mudacl exit code $? | tee -a $TEST_RESULTS
validator/bin/test.sh
echo Validator exit code $? | tee -a $TEST_RESULTS

# Runs lint checks and some similar things
echo Lint checks | tee -a $TEST_RESULTS
cmd/inbuild skip
echo cmd/inbuild exit code $? | tee -a $TEST_RESULTS

echo Extended tests | tee -a $TEST_RESULTS
cp misc/system_multi.conf local/system.conf
cat <<EOF >> local/system.conf
fail_hook=misc/dump_network.sh
test_config=misc/runtime_configs/long_wait
host_tests=misc/all_tests.conf
site_path=misc/test_site
site_reports=local/tmp
startup_faux_1_opts=brute
startup_faux_2_opts=nobrute
startup_faux_3_opts=bacnet
EOF
cmd/run -b -s
tail -qn 1 inst/run-port-*/nodes/bacext*/tmp/report.txt | tee -a $TEST_RESULTS
tail -qn 1 inst/run-port-*/nodes/brute*/tmp/report.txt | tee -a $TEST_RESULTS
more inst/run-port-*/scans/dhcp_triggers.txt | cat
dhcp_short=$(fgrep pass inst/run-port-01/scans/dhcp_triggers.txt | wc -l)
dhcp_long=$(fgrep long inst/run-port-01/scans/dhcp_triggers.txt | wc -l)
echo dhcp requests $dhcp_short $dhcp_long | tee -a $TEST_RESULTS
sort inst/result.log | tee -a $TEST_RESULTS
more inst/run-port-*/nodes/ping*/activate.log | cat
more inst/run-port-*/nodes/nmap*/activate.log | cat
more inst/run-port-*/nodes/brute*/activate.log | cat
ls inst/fail_fail01/ | tee -a $TEST_RESULTS
jq .modules inst/run-port-02/nodes/ping02/tmp/module_config.json | tee -a $TEST_RESULTS

function redact {
    sed -e 's/\s*%%.*//' \
        -e 's/2019-.*T.*Z/XXX/' \
        -e 's/DAQ version.*//'
}

cat docs/device_report.md | redact > out/redacted_docs.md
cat inst/reports/report_9a02571e8f01_*.md | redact > out/redacted_file.md

echo Redacted docs diff | tee -a $TEST_RESULTS
(diff out/redacted_docs.md out/redacted_file.md && echo No report diff) | tee -a $TEST_RESULTS

echo Done with tests | tee -a $TEST_RESULTS
