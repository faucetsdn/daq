#!/bin/bash

source testing/test_preamble.sh

echo DHCP Tests >> $TEST_RESULTS

cp misc/system_multi.conf local/system.conf

cat <<EOF >> local/system.conf
monitor_scan_sec=1
startup_faux_1_opts=
startup_faux_2_opts="xdhcp"
startup_faux_3_opts=
EOF

intf_mac="9a02571e8f03"
rm -rf local/site
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

intf_mac="9a02571e8f04"
mkdir -p local/site/mac_addrs/$intf_mac
cat <<EOF > local/site/mac_addrs/$intf_mac/module_config.json
{
  "modules": {
    "ipaddr": {
      "timeout_sec": 320,
      "dhcp_mode": "ip_change"
    }
  }
}
EOF


cmd/run -b -s settle_sec=0 dhcp_lease_time=120s

cat inst/result.log | tee -a $TEST_RESULTS

for iface in $(seq 1 4); do
    intf_mac=9a:02:57:1e:8f:0$iface
    ip_file=inst/run-port-0$iface/scans/ip_triggers.txt
    cat $ip_file
    ip_triggers=$(fgrep done $ip_file | wc -l)
    long_triggers=$(fgrep long $ip_file | wc -l)
    num_ips=$((cat $ip_file | cut -d ' ' -f 1 | sort | uniq | wc -l))
    echo Found $ip_triggers ip triggers and $long_triggers long ip responses.
    if [ $iface == 4 ]; then
        echo "Device $iface ip triggers: $(((ip_triggers + long_triggers) >= 2))" | tee -a $TEST_RESULTS
        echo "Number of ips: $num_ips"
    else
      echo "Device $iface ip triggers: $((ip_triggers > 0)) $((long_triggers > 0))" | tee -a $TEST_RESULTS
    fi
done

echo Done with tests | tee -a $TEST_RESULTS
