#!/bin/bash

source testing/test_preamble.sh

echo DHCP Tests >> $TEST_RESULTS

cat <<EOF > local/system.conf
include=../config/system/default.yaml
site_description="Multi-Device Configuration"
switch_setup.uplink_port=7
interfaces.faux-1.opts=
interfaces.faux-2.opts=xdhcp
interfaces.faux-3.opts=
interfaces.faux-4.opts=
interfaces.faux-5.opts=
interfaces.faux-6.opts=
monitor_scan_sec=1
EOF

intf_mac="9a02571e8f03"
rm -rf local/site
mkdir -p local/site/mac_addrs/$intf_mac
cat <<EOF > local/site/mac_addrs/$intf_mac/device_config.json
{
  "modules": {
    "ipaddr": {
      "timeout_sec": 320,
      "dhcp_mode": "LONG_RESPONSE"
    }
  }
}
EOF

# Multi subnet tests
intf_mac="9a02571e8f04"
mkdir -p local/site/mac_addrs/$intf_mac
cat <<EOF > local/site/mac_addrs/$intf_mac/device_config.json
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

# ip and dhcp change tests
intf_mac="9a02571e8f05"
mkdir -p local/site/mac_addrs/$intf_mac
cat <<EOF > local/site/mac_addrs/$intf_mac/device_config.json
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

# DHCP times out in extended DHCP tests
intf_mac="9a02571e8f06"
mkdir -p local/site/mac_addrs/$intf_mac
cat <<EOF > local/site/mac_addrs/$intf_mac/device_config.json
{
  "modules": {
    "ipaddr": {
      "enabled": true,
      "timeout_sec": 0,
      "port_flap_timeout_sec": 20,
      "dhcp_ranges": []
    }
  }
}
EOF

function kill_dhcp_client {
    CONTAINER=$1
    pid=$(docker exec $CONTAINER ps aux | grep dhclient | awk '{print $2}')
    echo Killing dhcp client in $CONTAINER pid $pid
    docker exec $CONTAINER kill $pid
}

# Check that killing the dhcp client on a device times out the ipaddr test.
monitor_log "Target port 6 connect successful" "kill_dhcp_client daq-faux-6"
build_if_not_release
cmd/run -s settle_sec=0 dhcp_lease_time=120s

cat inst/result.log | sort | tee -a $TEST_RESULTS

for iface in $(seq 1 6); do
    intf_mac=9a:02:57:1e:8f:0$iface
    ip_file=inst/run-9a02571e8f0$iface/scans/ip_triggers.txt
    report_file=inst/run-9a02571e8f0$iface/nodes/ipaddr0$iface/tmp/report.txt
    base_log=inst/run-9a02571e8f0$iface/nodes/ipaddr0$iface/activate.log
    activate_log=inst/run-9a02571e8f0$iface/nodes/ipaddr0$iface/tmp/activate.log
    more $ip_file $report_file $base_log $activate_log | cat
    ip_triggers=$(fgrep done $ip_file | wc -l)
    long_triggers=$(fgrep long $ip_file | wc -l)
    num_ips=$(cat $ip_file | cut -d ' ' -f 1 | sort | uniq | wc -l)
    dhcp_change=$(cat $report_file | fgrep 'pass connection.ipaddr.disconnect_ip_change' | wc -l)
    ip_change=$(cat $report_file | fgrep 'pass connection.ipaddr.ip_change' | wc -l)
    echo Found $ip_triggers ip triggers and $long_triggers long ip responses.
    if [ $iface == 6 ]; then
      device_dhcp_timeouts=$(fgrep 'dhcp timeout after 120s lease time' $activate_log | wc -l)
      echo "Device $iface dhcp timeouts: $device_dhcp_timeouts" | tee -a $TEST_RESULTS
      echo "Device $iface ip change: $((ip_change))" | tee -a $TEST_RESULTS
      echo "Device $iface dhcp change: $((dhcp_change))" | tee -a $TEST_RESULTS
    elif [ $iface == 5 ]; then
      echo "Device $iface ip triggers: $(((ip_triggers + long_triggers) >= 3))" | tee -a $TEST_RESULTS
      echo "Device $iface num of ips: $num_ips" | tee -a $TEST_RESULTS
      echo "Device $iface ip change: $((ip_change))" | tee -a $TEST_RESULTS
      echo "Device $iface dhcp change: $((dhcp_change))" | tee -a $TEST_RESULTS
    elif [ $iface == 4 ]; then
      echo "Device $iface ip triggers: $(((ip_triggers + long_triggers) >= 4))" | tee -a $TEST_RESULTS
      subnet1_ip=$(fgrep "ip notification 192.168." $activate_log | wc -l)
      subnet2_ip=$(fgrep "ip notification 10.255.255." $activate_log | wc -l)
      subnet3_ip=$(fgrep "ip notification 172.16.0." $activate_log | wc -l)
      uniq_subnet_ips=$(fgrep "ip notification 172.16.0." $activate_log | awk '{print $6}' | uniq | wc -l)
      echo "Device $iface subnet 1 ip: $subnet1_ip subnet 2 ip: $subnet2_ip subnet 3 ip: $subnet3_ip ip_changed: $((uniq_subnet_ips > 1))" | tee -a $TEST_RESULTS
    elif [ $iface == 3 ]; then
      echo "Device $iface long ip triggers: $((long_triggers > 0))" | tee -a $TEST_RESULTS
    else
      echo "Device $iface ip triggers: $((ip_triggers > 0)) $((long_triggers > 0))" | tee -a $TEST_RESULTS
    fi

done

echo Done with tests | tee -a $TEST_RESULTS
