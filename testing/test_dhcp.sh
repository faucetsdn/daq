#!/bin/bash

source testing/test_preamble.sh

# num of devices need to less than 10
NUM_DEVICES=8
RUN_LIMIT=20
# num of timeout devices need to be less or equal to num dhcp devices 
NUM_LONG_DHCP_DEVICES=3
echo DHCP Tests >> $TEST_RESULTS

echo source misc/system.conf > local/system.conf

manystartup=inst/startup_many.cmd
rm -f $manystartup
echo startup_cmds=$manystartup >> local/system.conf

echo monitor_scan_sec=5 >> local/system.conf
echo sec_port=$((NUM_DEVICES+1)) >> local/system.conf

ifaces=
for iface in $(seq 1 $NUM_DEVICES); do
    ifaces=${ifaces},faux-$iface
    if [[ $iface -le $NUM_LONG_DHCP_DEVICES ]]; then
        ip="10.20.0.$((iface+5))"
        intf_mac="9a02571e8f0$iface"
        mkdir -p local/site/mac_addrs/$intf_mac
            cat <<EOF > local/site/mac_addrs/$intf_mac/module_config.json
    {
        "modules": {
            "ipaddr": {
                "timeout_sec": 320,
                "dhcp_mode": "long_response"
            }
        }
    }
EOF
    fi
    echo autostart cmd/faux $iface $xdhcp>> $manystartup
done
echo intf_names=${ifaces#,} >> local/system.conf

echo DAQ stress test | tee -a $TEST_RESULTS
# Limit should be ~30, but something is wrong with startup sequence.
cmd/run -b run_limit=$RUN_LIMIT settle_sec=0 dhcp_lease_time=120s
cat inst/result.log
results=$(fgrep [] inst/result.log | wc -l)
echo Found $results successful runs.
echo Enough results: $((results >= 6*RUN_LIMIT/10)) | tee -a $TEST_RESULTS

for i in $(seq 1 $NUM_LONG_DHCP_DEVICES); do 
    intf_mac="9a:02:57:1e:8f:0$i"
    ip_triggers=$(egrep -i "IP activating target $intf_mac" inst/cmdrun.log | wc -l)
    long_ip_triggers=$(egrep -i "IP notify.*gw0$i \(long/" inst/cmdrun.log | wc -l)
    echo "Device $i enough long ip triggers? $((ip_triggers == long_ip_triggers && long_ip_triggers > 1))" | tee -a $TEST_RESULTS
done

# This is broken -- should have many more results available!
echo Done with tests | tee -a $TEST_RESULTS
