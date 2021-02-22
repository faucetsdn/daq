#!/bin/bash

source testing/test_preamble.sh

echo Switch Tests >> $TEST_RESULTS

rm -rf inst/tmp_site && mkdir -p inst/tmp_site
cp resources/setups/baseline/report_template.md inst/tmp_site/

release_tag=`git describe --dirty || echo unknown`
build_mode=
# If the current commit is a release tag, then pull images.
echo Processing release tag $release_tag
if [[ "$release_tag" != unknown && ! "$release_tag" =~ -.*- ]]; then
    build_mode=pull
fi
cmd/build $build_mode build

echo %%%%%%%%%%%%%%%%%%%%%% External switch tests | tee -a $TEST_RESULTS
echo 'include: ../config/system/ext.yaml' > local/system.yaml
cmd/run -s
cat inst/result.log | tee -a $TEST_RESULTS
fgrep dp_id inst/faucet.yaml | tee -a $TEST_RESULTS
fgrep -i switch inst/run-9a02571e8f00/nodes/ping*/activate.log | sed -e "s/\r//g" | tee -a $TEST_RESULTS
cat -vet inst/run-9a02571e8f00/nodes/ping*/activate.log
count=$(fgrep icmp_seq=5 inst/run-9a02571e8f00/nodes/ping*/activate.log | wc -l)
echo switch ping $count | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%% Alt switch tests | tee -a $TEST_RESULTS
echo 'include: ../config/system/alt.yaml' > local/system.yaml
cmd/faucet

timeout 1200s cmd/run -s

fgrep 'Learned 9a:02:57:1e:8f:01 on vid 1002' inst/cmdrun.log | head -1 | redact | tee -a $TEST_RESULTS
unqie_ips=$(fgrep '10.20.99' inst/run-9a02571e8f01/scans/ip_triggers.txt | awk '{print $1}' | sort | uniq | wc -l)
echo Unique IPs: $unqie_ips | tee -a $TEST_RESULTS

fgrep RESULT inst/run-9a02571e8f01/nodes/ping01/activate.log | tee -a $TEST_RESULTS

# acquire test will fail since the DHCP server never even tries
fgrep 9a02571e8f02 inst/result.log | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%% Done with tests | tee -a $TEST_RESULTS
