#!/bin/bash

source testing/test_preamble.sh

# num of devices need to less than 10
NUM_DEVICES=8
RUN_LIMIT=20
# num of timeout devices need to be less or equal to num dhcp devices
NUM_NO_DHCP_DEVICES=4
NUM_TIMEOUT_DEVICES=2
echo Many Tests >> $TEST_RESULTS

echo source config/system/default.yaml > local/system.conf

echo monitor_scan_sec=5 >> local/system.conf
echo switch_setup.uplink_port=$((NUM_DEVICES+1)) >> local/system.conf
echo gcp_cred=$gcp_cred >> local/system.conf

for iface in $(seq 1 $NUM_DEVICES); do
    xdhcp=""
    if [[ $iface -le $NUM_NO_DHCP_DEVICES ]]; then
        ip="10.20.0.$((iface+5))"
        intf_mac="9a02571e8f0$iface"
        xdhcp="xdhcp=$ip"
        mkdir -p local/site/mac_addrs/$intf_mac
        if [[ $iface -gt $NUM_TIMEOUT_DEVICES ]]; then
            #Install site specific configs for xdhcp ips
            cat <<EOF > local/site/mac_addrs/$intf_mac/module_config.json
    {
        "static_ip": "$ip"
    }
EOF
        else
            cat <<EOF > local/site/mac_addrs/$intf_mac/module_config.json
    {
        "modules": {
            "ipaddr": {
              "timeout_sec": 320
            }
        }
    }
EOF
        fi
    fi
    echo interfaces.faux-$iface.opts=$xdhcp >> local/system.conf
done

echo DAQ stress test | tee -a $TEST_RESULTS

start_time=`date -u -Isec`
cmd/run -b run_limit=$RUN_LIMIT settle_sec=0 dhcp_lease_time=120s
end_time=`date -u -Isec`

cat inst/result.log
results=$(fgrep [] inst/result.log | wc -l)
timeouts=$(fgrep "ipaddr:TimeoutError" inst/result.log | wc -l)

cat inst/run-port-*/scans/ip_triggers.txt
static_ips=$(fgrep nope inst/run-port-*/scans/ip_triggers.txt | wc -l)

more inst/run-port-*/nodes/ping*/activate.log | cat

echo Found $results clean runs, $timeouts timeouts, and $static_ips static_ips.

# This is broken -- should have many more results available!
echo Enough results: $((results >= 6*RUN_LIMIT/10)) | tee -a $TEST_RESULTS

# $timeouts should strictly equal $NUM_TIMEOUT_DEVICES when dhcp step is fixed.
echo Enough DHCP timeouts: $((timeouts >= NUM_TIMEOUT_DEVICES)) | tee -a $TEST_RESULTS
echo Enough static ips: $((static_ips >= (NUM_NO_DHCP_DEVICES - NUM_TIMEOUT_DEVICES))) | tee -a $TEST_RESULTS

echo bin/combine_reports device=9a:02:57:1e:8f:05 from_time=$start_time to_time=$end_time count=2
bin/combine_reports device=9a:02:57:1e:8f:05 from_time=$start_time to_time=$end_time count=2

cat inst/reports/combo_*.md

redact < docs/soak_report.md > out/redacted_soak.md
redact < inst/reports/combo_*.md > out/redacted_many.md
echo Redacted soak diff | tee -a $TEST_RESULTS
(diff out/redacted_soak.md out/redacted_many.md && echo No soak report diff) \
    | tee -a $TEST_RESULTS

if [ -f "$gcp_cred" ]; then
    mv inst/reports/combo_*.md out/report_local.md
    echo Pulling reports from gcp...
    bin/combine_reports device=9a:02:57:1e:8f:05 from_time=$start_time to_time=$end_time \
        count=2 from_gcp=true
    echo GCP results diff | tee -a $GCP_RESULTS
    diff inst/reports/combo_*.md out/report_local.md | tee -a $GCP_RESULTS
fi

echo Done with many | tee -a $TEST_RESULTS
