#!/bin/bash

source testing/test_preamble.sh

# num of devices need to less than 10
NUM_DEVICES=9
RUN_LIMIT=20
# num of timeout devices need to be less or equal to num dhcp devices
NUM_NO_DHCP_DEVICES=4
NUM_TIMEOUT_DEVICES=2

# Extended DHCP tests
NUM_IPADDR_TEST_DEVICES=2
NUM_IPADDR_TEST_TIMEOUT_DEVICES=1

echo Many Tests >> $TEST_RESULTS

echo include=../config/system/default.yaml > local/system.conf
echo monitor_scan_sec=5 >> local/system.conf
# Limit subnet to test mininet ip reuse.
echo internal_subnet.subnet=10.20.0.0/27 >> local/system.conf
echo switch_setup.of_dpid=2 >> local/system.conf
echo switch_setup.uplink_port=$((NUM_DEVICES+1)) >> local/system.conf
echo gcp_cred=$gcp_cred >> local/system.conf
echo dhcp_lease_time=120s >> local/system.conf
echo base_conf=resources/setups/orchestration/base_config.json >> local/system.conf

mkdir -p local/site/
cat <<EOF > local/site/site_config.json
{
  "modules": {
    "ipaddr": {
      "enabled": true,
      "timeout_sec": 0,
      "port_flap_timeout_sec": 20,
      "dhcp_ranges": [
        {"start": "192.168.0.1", "end": "192.168.255.254", "prefix_length": 16},
        {"start": "172.16.0.1", "end": "172.31.255.254", "prefix_length": 12},
        {"start": "10.0.0.1", "end": "10.255.255.254", "prefix_length": 8}
      ]
    }
  }
}
EOF

for iface in $(seq 1 $NUM_DEVICES); do
    xdhcp=""
    intf_mac="9a02571e8f0$iface"
    mkdir -p local/site/mac_addrs/$intf_mac
    if [[ $iface -le $NUM_NO_DHCP_DEVICES ]]; then
        ip="10.20.255.$((iface+5))"
        xdhcp="xdhcp=$ip opendns ntp_fail"
        if [[ $iface -gt $NUM_TIMEOUT_DEVICES ]]; then
            #Install site specific configs for xdhcp ips
            cat <<EOF > local/site/mac_addrs/$intf_mac/device_config.json
    {
        "static_ip": "$ip",
        "modules": {
            "ipaddr": {
                "enabled": false
            }
        }
    }
EOF
        else
            cat <<EOF > local/site/mac_addrs/$intf_mac/device_config.json
    {
        "modules": {
            "ipaddr": {
                "enabled": false,
                "timeout_sec": 320
            }
        }
    }
EOF
        fi
    elif [[ $iface -le $((NUM_NO_DHCP_DEVICES + NUM_IPADDR_TEST_DEVICES)) ]]; then
        if [[ $iface -le $((NUM_NO_DHCP_DEVICES + NUM_IPADDR_TEST_TIMEOUT_DEVICES)) ]]; then
            cat <<EOF > local/site/mac_addrs/$intf_mac/device_config.json
    {
        "modules": {
            "ipaddr": {
                "timeout_sec": 1
            }
        }
    }
EOF
        else
            cat <<EOF > local/site/mac_addrs/$intf_mac/device_config.json
    {
        "modules": {
            "ipaddr": {
                "enabled": false
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
build_if_not_release
cmd/run run_limit=$RUN_LIMIT settle_sec=0 dhcp_lease_time=120s
end_time=`date -u -Isec --date="+5min"` # Adding additional time to account for slower cloud function calls for updating timestamp.

cat inst/result.log
results=$(fgrep [] inst/result.log | wc -l)
timeouts=$(fgrep "ipaddr:TimeoutError" inst/result.log | wc -l)
ipaddr_timeouts=$(fgrep "ipaddr:TimeoutError" inst/result.log | wc -l)

fgrep "ip notification" inst/run-*/nodes/ipaddr*/tmp/module.log
ip_notifications=$(fgrep "ip notification" inst/run-*/nodes/ipaddr*/tmp/module.log | wc -l)
alternate_subnet_ip=$(fgrep "ip notification 192.168." inst/run-*/nodes/ipaddr*/tmp/module.log | wc -l)

cat inst/run-*/scans/ip_triggers.txt
static_ips=$(fgrep nope inst/run-*/scans/ip_triggers.txt | wc -l)
ntp_traffic=$(fgrep "RESULT fail base.startup.ntp" inst/run-*/nodes/ping*/tmp/result_lines.txt | wc -l)
dns_traffic=$(fgrep "RESULT fail base.startup.dns" inst/run-*/nodes/ping*/tmp/result_lines.txt | wc -l)

more inst/run-*/nodes/ping*/activate.log | cat
more inst/run-*/nodes/ipaddr*/tmp/module.log | cat

echo Found $results clean runs, $timeouts timeouts, and $static_ips static_ips.
echo ipaddr had $ip_notifications notifications, $ipaddr_timeouts timeouts, and $alternate_subnet_ip alternates.

# This is broken -- should have many more results available!
echo Enough results: $((results >= 5*RUN_LIMIT/10)) | tee -a $TEST_RESULTS

# $timeouts should strictly equal $NUM_TIMEOUT_DEVICES when dhcp step is fixed.
echo Enough DHCP timeouts: $((timeouts >= NUM_TIMEOUT_DEVICES)) | tee -a $TEST_RESULTS
echo Enough static ips: $((static_ips >= (NUM_NO_DHCP_DEVICES - NUM_TIMEOUT_DEVICES))) | tee -a $TEST_RESULTS
echo Found NTP and DNS traffic for static ip devices: $((ntp_traffic > 0)) $((dns_traffic > 0)) | tee -a $TEST_RESULTS

echo Enough ipaddr tests: $((ip_notifications >= (NUM_IPADDR_TEST_DEVICES - NUM_IPADDR_TEST_TIMEOUT_DEVICES) * 2 )) | tee -a $TEST_RESULTS
echo Enough alternate subnet ips: $((alternate_subnet_ip >= (NUM_IPADDR_TEST_DEVICES - NUM_IPADDR_TEST_TIMEOUT_DEVICES) )) | tee -a $TEST_RESULTS
echo Enough ipaddr timeouts: $((ipaddr_timeouts >= NUM_IPADDR_TEST_TIMEOUT_DEVICES)) | tee -a $TEST_RESULTS

combine_cmd="bin/combine_reports device=9a:02:57:1e:8f:05 from_time=$start_time to_time=$end_time count=2"
echo $combine_cmd
$combine_cmd

cat inst/reports/combo_*.md

redact < docs/soak_report.md > out/redacted_soak.md
redact < inst/reports/combo_*.md > out/redacted_many.md
echo Redacted soak diff | tee -a $TEST_RESULTS
(diff out/redacted_soak.md out/redacted_many.md && echo No soak report diff) \
    | tee -a $TEST_RESULTS

if [ -f "$gcp_cred" ]; then
    mv inst/reports/combo_*.md out/report_local.md
    echo '******Local reports******'
    ls -l inst/reports/report_9a02571e8f05*.md
    echo '*************************'

    daq_run_id=$(< inst/daq_run_id.txt)
    echo Pulling reports from gcp for daq RUN id $daq_run_id
    gcp_extras="daq_run_id=$daq_run_id from_gcp=true"
    echo $combine_cmd $gcp_extras
    $combine_cmd $gcp_extras
    echo GCP results diff | tee -a $GCP_RESULTS
    diff inst/reports/combo_*.md out/report_local.md | tee -a $GCP_RESULTS
fi

echo Done with many | tee -a $TEST_RESULTS
