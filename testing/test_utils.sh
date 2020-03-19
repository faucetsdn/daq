#!/bin/bash

# Create system.conf and startup file for arbitrary number of faux virtual devices.
function generate {
  echo source misc/system.conf > local/system.conf

  type=$1
  faux_num=$2

  echo Running $type $faux_num | tee -a $TEST_RESULTS

  # Clean out in case there's an error
  rm -rf inst/run-port-*
  rm -rf inst/runtime_conf

  topostartup=inst/startup_topo.cmd
  rm -f $topostartup
  echo startup_cmds=$topostartup >> local/system.conf

  echo sec_port=$((faux_num+1)) >> local/system.conf

  # Create required number of faux devices
  iface_names=
  for iface in $(seq 1 $faux_num); do
      iface_names=${iface_names},faux-$iface
      echo autostart cmd/faux $iface discover >> $topostartup
  done
  echo intf_names=${iface_names#,} >> local/system.conf

  # Specify a different set of tests
  echo host_tests=misc/topo_tests.conf >> local/system.conf

  echo site_description=\"$type with $devices devices\" >> local/system.conf
  echo device_specs=misc/device_specs/topo_$type.json >> local/system.conf
  echo test_config=inst/runtime_conf/ >> local/system.conf
  # Don't use default monitor scan to get both src/dst traffic.
  echo monitor_scan_sec=0 >> local/system.conf
  echo port_debounce_sec=0 >> local/system.conf
}

function check_setup {
    src_dev=$1
    conf_dir=inst/runtime_conf/port-$(printf %02d $src_dev)
    cmd_file=$conf_dir/ping_runtime.sh
    echo $cmd_file
    if [ -f $cmd_file ]; then
        return
    fi
    mkdir -p $conf_dir

    cat >> $cmd_file <<EOF
timeout 30 tcpdump -eni \$HOSTNAME-eth0 -w /tmp/eth0.pcap || true
function test_bacnet {
    bacnet_base="tcpdump -en -r /tmp/eth0.pcap port 47808"
    echo \$((\$(\$bacnet_base and \$@ | wc -l ) > 0))
}
function test_tcp {
    src_mac=$MAC_BASE:$(printf %02x $src_dev)
    dst_mac=$MAC_BASE:\$(printf %02x \$1)
    # Check for TCP ACKs, since that means the network is allowing it.
    tcp_base="tcpdump -en -r /tmp/eth0.pcap tcp and ether dst \$src_mac"
    filter="ether src \$dst_mac and src port \$2"
    echo \$((\$(\$tcp_base and \$filter | wc -l ) > 0))
}
EOF
}

function check_bacnet {
    src_dev=$(printf %02d $1)
    dst_dev=$(printf %02d $2)
    shift
    shift
    expected="$*"

    src_mac=$MAC_BASE:$(printf %02x $src_dev)
    dst_mac=$MAC_BASE:$(printf %02x $dst_dev)

    cmd_file=$(check_setup $src_dev)

    cat >> $cmd_file <<EOF
ether_dst=\$(test_bacnet ether dst $dst_mac)
ether_not=\$(test_bacnet not ether src $src_mac and not ether dst $src_mac)
bcast_src=\$(test_bacnet ether broadcast and ether src $src_mac)
bcast_oth=\$(test_bacnet ether broadcast and not ether src $src_mac)
result="\$ether_dst \$ether_not \$bcast_src \$bcast_oth"
echo check_bacnet $src_dev $dst_dev \$result | tee -a $bacnet_file
[ -z "$expected" -o "$expected" == "\$result" ] || (echo \$result != $expected && false)
EOF
}

function check_socket {
    src_dev=$1
    dst_dev=$2
    shift
    shift
    expected="$*"

    src_host=daq-faux-$(printf %d $src_dev)
    dst_host=daq-faux-$(printf %d $dst_dev)

    faux_dir=inst/runtime_conf/$src_host
    mkdir -p $faux_dir
    conf_dir=inst/runtime_conf/port-$(printf %02d $src_dev)
    mkdir -p $conf_dir

    start_faux=$faux_dir/start_faux.sh
    for port in 23 443; do
        echo "(while sleep 5; do timeout 5 nc $dst_host $port; done) &" >> $start_faux
    done

    cmd_file=$(check_setup $src_dev)
    cat >> $cmd_file <<EOF
telnet=\$(test_tcp $dst_dev 23)
https=\$(test_tcp $dst_dev 443)
result="\$telnet \$https"
echo check_socket $src_dev $dst_dev \$result >> $socket_file
[ -z "$expected" -o "$expected" == "\$result" ] || (echo \$result != $expected && false)
EOF
}

function run_test {
    for port in $(seq 1 $1); do
        conf_dir=inst/runtime_conf/port-$(printf %02d $port)
        cmd_file=$conf_dir/ping_runtime.sh
        test -d $conf_dir || (mkdir -p $conf_dir; echo sleep 30 >> $cmd_file)
    done
    cmd/run -s
    fgrep :ping: inst/result.log | tee -a $TEST_RESULTS
    cat inst/run-port-*/nodes/ping*${socket_file} | tee -a $TEST_RESULTS
    cat inst/run-port-*/nodes/ping*${bacnet_file} | tee -a $TEST_RESULTS
    more inst/run-port-*/nodes/ping*/activate.log | cat
}
