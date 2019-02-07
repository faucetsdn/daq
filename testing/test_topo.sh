#!/bin/bash

source testing/test_preamble.sh

echo Topology Tests >> $TEST_RESULTS

# Create system.conf and startup file for arbitrary number of faux virtual devices.
function generate_system {
  echo source misc/system.conf > local/system.conf

  # The number of faux devices is expressed in the FAUX_NUM variable
  FAUX_NUM=$1

  topostartup=inst/startup_topo.cmd
  rm -f $topostartup
  echo startup_cmds=$topostartup >> local/system.conf

  # Specify the secondary port as number of faux devices + 1
  echo sec_port=`echo $FAUX_NUM+1 | bc` >> local/system.conf

  # Create arbitrary number of faux devices
  ifaces=
  for iface in $(eval echo {1..$FAUX_NUM}); do
      ifaces=${ifaces},faux-$iface
      echo autostart cmd/faux $iface discover >> $topostartup
  done
  echo intf_names=${ifaces#,} >> local/system.conf
  # Specify a different set of tests
  echo host_tests=misc/topo_tests.conf >> local/system.conf
}

echo DAQ topologies test | tee -a $TEST_RESULTS

# Ensure that all the ACLs have been generated
bin/mudacl

minimal_device_traffic="tcpdump -en -r inst/run-port-01/scans/monitor.pcap port 47808"
minimal_device_bcast="$minimal_device_traffic and ether broadcast"
minimal_device_ucast="$minimal_device_traffic and ether dst 9a:02:57:1e:8f:02"
minimal_device_xcast="$minimal_device_traffic and ether host 9a:02:57:1e:8f:03"
minimal_cntrlr_traffic="tcpdump -en -r inst/run-port-02/scans/monitor.pcap port 47808"
minimal_cntrlr_bcast="$minimal_cntrlr_traffic and ether broadcast"
minimal_cntrlr_ucast="$minimal_cntrlr_traffic and ether dst 9a:02:57:1e:8f:01"
minimal_cntrlr_xcast="$minimal_cntrlr_traffic and ether host 9a:02:57:1e:8f:03"

function test_topo {
    type=$1
    devices=$2
    echo "Generate system topology for system $type and $devices devices"
    generate_system $devices
    echo "Running DAQ tests"
    cmd/run -s site_description=$type device_specs=misc/device_specs_topo_$type.json
    # TODO: include additional test results checks and print them in test results file
    # For reference, faux devices MAC addresses are in the form 9a:02:57:1e:8f:XX
    bcast=$(eval echo \$$type\_device_bcast | wc -l)
    ucast=$(eval echo \$$type\_device_ucast | wc -l)
    xcast=$(eval echo \$$type\_device_xcast | wc -l)
    echo device $type $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS
    bcast=$(eval echo \$$type\_cntrlr_bcast | wc -l)
    ucast=$(eval echo \$$type\_cntrlr_ucast | wc -l)
    xcast=$(eval echo \$$type\_cntrlr_xcast | wc -l)
    echo cntrlr $type $(($bcast > 2)) $(($ucast > 2)) $(($xcast > 0)) | tee -a $TEST_RESULTS
}

# Run tests. The first option is the name of the test, the second one is the number of devices
#test_topo one 1
test_topo minimal 3
#test_topo minimal_commissioning 4
#test_topo complete 6
#test_topo headend 11
#test_topo two_groups 11

echo Done with tests | tee -a $TEST_RESULTS
