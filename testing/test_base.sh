#!/bin/bash

source testing/test_preamble.sh

echo Base Tests >> $TEST_RESULTS

rm -rf inst/tmp_site && mkdir -p inst/tmp_site
cp resources/setups/baseline/report_template.md inst/tmp_site/

if ! docker images | fgrep daqf/networking; then
    cmd/build
fi

echo %%%%%%%%%%%%%%%%%%%%%% Alt switch tests | tee -a $TEST_RESULTS
cp config/system/alt.yaml local/system.yaml
cmd/faucet

# TODO: Replace this with proper test once VLAN-triggers are added.
function configure_networking {
    docker exec daq-networking-2 ifconfig eth0 down
    docker exec daq-networking-2 ifconfig faux-eth0 up
    docker exec daq-networking-2 ip addr add 10.20.255.254/16 dev faux-eth0
    docker exec daq-networking-2 bash -c "echo dhcp-range=10.20.99.100,10.20.99.254 >> /etc/dnsmasq.conf"
}

function restart_networking {
    docker exec daq-networking-2 bash -c "./autorestart_dnsmasq &"
}

monitor_log "Added link faux-2 as port 3 on alt-switch" configure_networking
monitor_log "Target device 9a02571e8f01 waiting for ip" restart_networking
timeout 1200s cmd/run -n
fgrep '9a:02:57:1e:8f:01 learned on vid 1002' inst/cmdrun.log | head -1 | redact | tee -a $TEST_RESULTS
correct_ips=$(fgrep '10.20.99' inst/run-9a02571e8f01/scans/ip_triggers.txt | wc -l)
echo Correct IP: $correct_ips | tee -a $TEST_RESULTS
cat inst/result.log | grep 9a02571e8f01 | tee -a $TEST_RESULTS
# ping test should fail since there are no dhcp packets captured

echo %%%%%%%%%%%%%%%%%%%%%% Done with tests | tee -a $TEST_RESULTS
