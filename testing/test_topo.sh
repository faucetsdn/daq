#!/bin/bash

source testing/test_preamble.sh

echo Topology Tests >> $TEST_RESULTS

# Create system.conf and startup file for arbitrary number of faux virtual devices.
function generate_system {
  echo source misc/system.conf > local/system.conf

  type=$1
  faux_num=$2

  topostartup=inst/startup_topo.cmd
  rm -f $topostartup
  echo startup_cmds=$topostartup >> local/system.conf

  echo sec_port=$((faux_num+1)) >> local/system.conf

  # Create required number of faux devices
  for iface in $(seq 1 $faux_num); do
      iface_names=${iface_names},faux-$iface
      echo autostart cmd/faux $iface discover >> $topostartup
  done
  echo intf_names=${iface_names#,} >> local/system.conf

  # Specify a different set of tests
  echo host_tests=misc/topo_tests.conf >> local/system.conf

  echo site_description=\"$type with $devices devices\" >> local/system.conf
  echo device_specs=misc/device_specs_topo_$type.json >> local/system.conf
}

MAC_BASE=9a:02:57:1e:8f

function check_bacnet {
    at_dev=$(printf %02d $1)
    ex_dev=$(printf %02d $2)

    at_mac=$MAC_BASE:$(printf %02x $at_dev)
    ex_mac=$MAC_BASE:$(printf %02x $ex_dev)

    tcp_base="tcpdump -en -r inst/run-port-$at_dev/scans/monitor.pcap port 47808"

    ucast_to=`$tcp_base and ether dst $ex_mac | wc -l`
    ucast_cross=`$tcp_base and not ether src $at_mac and not ether dst $at_mac | wc -l`
    bcast_out=`$tcp_base and ether broadcast and ether src $at_mac | wc -l`

    # Monitoring is currently broken, so only captures outgoing packets, so this doesn't work.
    bcast_from=`$tcp_base and ether broadcast and ether src $ex_mac | wc -l`

    echo bacnet $at_dev/$ex_dev $((ucast_to > 0)) $((ucast_cross > 0)) $((bcast_out > 0)) | tee -a $TEST_RESULTS
}

function run_topo {
    type=$1
    devices=$2

    # Clean out in case there's an error
    rm -rf inst/run-port-*

    echo Running $type $devices | tee -a $TEST_RESULTS
    generate_system $type $devices
    cmd/run -s
}

run_topo minimal 3
check_bacnet 1 2
check_bacnet 2 3
check_bacnet 3 1

echo Done with tests | tee -a $TEST_RESULTS
