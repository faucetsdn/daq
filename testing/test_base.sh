#!/bin/bash

source testing/test_preamble.sh

echo Base Tests >> $TEST_RESULTS

rm -rf inst/tmp_site && mkdir -p inst/tmp_site
cp resources/setups/baseline/report_template.md inst/tmp_site/
cp resources/test_site/site_config.json inst/tmp_site/site_config.json
cat <<EOF > inst/tmp_site/site_config.json
    {
        "modules": {
            "discover": {
                "enabled": false
            },
             "bacnet": {
                "enabled": false
            },
             "mudgee": {
                "enabled": false
            }
        }
    }
EOF

echo Creating MUD templates...
bin/mudacl

bin/build_proto check || exit 1

build_if_not_release

echo %%%%%%%%%%%%%%%%%%%%%% Base tests | tee -a $TEST_RESULTS
# Check that bringing down the trunk interface terminates DAQ.
rm -f local/system.yaml local/system.conf
MARKER=inst/run-9a02571e8f00/nodes/hold*/activate.log
monitor_marker $MARKER "sudo ip link set pri-eth1 down"
cmd/run -k -s site_path=inst/tmp_site
echo DAQ result code $? | tee -a $TEST_RESULTS
cat inst/result.log | tee -a $TEST_RESULTS

echo Redacted report for 9a02571e8f00:
cat inst/reports/report_9a02571e8f00_*.md | redact | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%% Test DAQ can recover from faucet restarts | tee -a $TEST_RESULTS
restart_faucet() {
    container=$(docker ps | grep daqf/faucet | awk '{print $1}')
    docker stop $container; sleep 5; docker start $container
}
monitor_log "Port 1 dpid 2 learned 9a:02:57:1e:8f:00" "restart_faucet"
cmd/run -s default_timeout_sec=100
reconnections=$(fgrep "Connecting to socket path" inst/cmdrun.log | wc -l)
echo Found reconnections? $((reconnections > 1)) | tee -a $TEST_RESULTS
cat inst/result.log | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%% Report Finalizing Exception handling | tee -a $TEST_RESULTS
# Check exception handling during report finalizing.
mv resources/setups/baseline/device_report.css resources/setups/baseline/device_report
cmd/run -s
mv resources/setups/baseline/device_report resources/setups/baseline/device_report.css
cat inst/result.log | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%% Telnet fail | tee -a $TEST_RESULTS
# Check that an open port causes the appropriate failure.
cmd/run -s interfaces.faux.opts=telnet
cat inst/result.log | tee -a $TEST_RESULTS
cat inst/run-9a02571e8f00/nodes/nmap01/activate.log
fgrep 'security.nmap.ports' inst/reports/report_9a02571e8f00_*.md | tee -a $TEST_RESULTS

echo %%%%%%%%%%%%%%%%%%%%%% Missing Docker Image | tee -a $TEST_RESULTS
# Check that an open port causes the appropriate failure.
docker rmi daqf/test_bacnet:latest # Check case of missing image
cmd/run -s 
echo DAQ result code $? | tee -a $TEST_RESULTS
cat inst/result.log | tee -a $TEST_RESULTS
tag=$(docker images daqf/test_bacnet | head -2 | tail -1 | awk '{print $3}')
docker tag daqf/test_bacnet:$tag daqf/test_bacnet:latest

echo %%%%%%%%%%%%%%%%%%%%%% Done with tests | tee -a $TEST_RESULTS
