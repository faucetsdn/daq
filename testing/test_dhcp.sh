#!/bin/bash

source testing/test_preamble.sh

echo DHCP Tests >> $TEST_RESULTS

cat <<EOF > local/system.conf
source config/system/default.yaml
site_description="Multi-Device Configuration"
switch_setup.uplink_port=6
interfaces.faux-1.opts=
interfaces.faux-2.opts=xdhcp
interfaces.faux-3.opts=
interfaces.faux-4.opts=
interfaces.faux-5.opts=
monitor_scan_sec=1
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

# Multi subnet multi subnet tests
intf_mac="9a02571e8f04"
mkdir -p local/site/mac_addrs/$intf_mac
cat <<EOF > local/site/mac_addrs/$intf_mac/module_config.json
{
  "modules": {
    "ipaddr": {
      "enabled": true,
      "port_flap_timeout_sec": 20,
      "dhcp_ranges": [{"start": "192.168.0.1", "end": "192.168.255.254", "prefix_length": 16}, 
        {"start": "10.255.255.1", "end": "10.255.255.255", "prefix_length": 24},
        {"start": "172.16.0.1", "end": "172.16.0.200", "prefix_length": 24}]
    }
  }
}
EOF

# ip change test
intf_mac="9a02571e8f05"
mkdir -p local/site/mac_addrs/$intf_mac
cat <<EOF > local/site/mac_addrs/$intf_mac/module_config.json
{
  "modules": {
    "ipaddr": {
      "enabled": true,
      "port_flap_timeout_sec": 20,
      "dhcp_ranges": []
    }
  }
}
EOF


cmd/run -b -s settle_sec=0 dhcp_lease_time=120s

cat inst/result.log | sort | tee -a $TEST_RESULTS

for iface in $(seq 1 5); do
    intf_mac=9a:02:57:1e:8f:0$iface
    ip_file=inst/run-port-0$iface/scans/ip_triggers.txt
    cat $ip_file
    ip_triggers=$(fgrep done $ip_file | wc -l)
    long_triggers=$(fgrep long $ip_file | wc -l)
    num_ips=$(cat $ip_file | cut -d ' ' -f 1 | sort | uniq | wc -l)
    echo Found $ip_triggers ip triggers and $long_triggers long ip responses.
    if [ $iface == 5 ]; then
      echo "Device $iface ip triggers: $(((ip_triggers + long_triggers) >= 3))" | tee -a $TEST_RESULTS
      echo "Device $iface num of ips: $num_ips" | tee -a $TEST_RESULTS
    elif [ $iface == 4 ]; then
      echo "Device $iface ip triggers: $(((ip_triggers + long_triggers) >= 4))" | tee -a $TEST_RESULTS
      subnet_ip=$(fgrep "ip notification 192.168" inst/run-port-*/nodes/ipaddr*/activate.log | wc -l)
      subnet2_ip=$(fgrep "ip notification 10.255.255" inst/run-port-*/nodes/ipaddr*/activate.log | wc -l)
      subnet3_ip=$(fgrep "ip notification 172.16.0" inst/run-port-*/nodes/ipaddr*/activate.log | wc -l)
      echo "Device $iface subnet 1 ip: $subnet_ip subnet 2 ip: $subnet2_ip subnet 3 ip: $subnet3_ip" | tee -a $TEST_RESULTS
    elif [ $iface == 3 ]; then
      echo "Device $iface long ip triggers: $((long_triggers > 0))" | tee -a $TEST_RESULTS
    else
      echo "Device $iface ip triggers: $((ip_triggers > 0)) $((long_triggers > 0))" | tee -a $TEST_RESULTS
    fi
done

echo Done with tests | tee -a $TEST_RESULTS
