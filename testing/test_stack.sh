#!/bin/bash

source testing/test_preamble.sh

out_dir=out/daq-test_stack
rm -rf $out_dir

t2sw1p6_pcap=$out_dir/t2sw1-eth6.pcap
t2sw1p7_pcap=$out_dir/t2sw1-eth7.pcap
nodes_dir=$out_dir/nodes

mkdir -p $out_dir $nodes_dir

ping_count=10
cap_length=$((ping_count + 20))

echo Generator tests | tee -a $TEST_RESULTS
rm -rf out/topology
bin/generate_topology raw_topo=topology/not-normal/nz-kiwi-ctr1 topo_dir=out/topology/normalized
diff -r out/topology/normalized topology/nz-kiwi-ctr1/ | tee -a $TEST_RESULTS

sites=$(cd topology; ls -d *)
mkdir -p out/topology/generated
for site in $sites; do
    if [ ! -f topology/$site/site_config.json ]; then
        continue;
    fi
    bin/generate_topology site_config=topology/$site/site_config.json topo_dir=out/topology/generated/$site
done
diff -r out/topology/generated topology/ | tee -a $TEST_RESULTS

function test_pair {
    src=$1
    dst=$2

    host=daq-faux-$src
    out_file=$nodes_dir/$host-$dst
    cmd="ping -c $ping_count 192.168.0.$dst"
    echo $host: $cmd
    echo -n $host: $cmd\ > $out_file
    docker exec $host $cmd | fgrep time= | fgrep -v DUP | wc -l >> $out_file 2>/dev/null &
}

function test_stack {
    mode=$1
    echo Testing stack mode $mode | tee -a $TEST_RESULTS
    bin/setup_stack $mode || exit 1

    # Restart one faucet instance to see if it goes crazy.
    #cmd/faucet nz-kiwi-ctr2 6673

    echo Capturing pcap to $t2sw1p6_pcap for $cap_length seconds...
    timeout $cap_length tcpdump -eni t2sw1-eth6 -w $t2sw1p6_pcap &
    timeout $cap_length tcpdump -eni t2sw1-eth7 -w $t2sw1p7_pcap &
    sleep 5

    echo Executing 2nd warm-up
    docker exec daq-faux-1 ping -c 3 192.168.0.2 &
    docker exec daq-faux-1 ping -c 3 192.168.0.3 &
    docker exec daq-faux-2 ping -c 3 192.168.0.1 &
    docker exec daq-faux-2 ping -c 3 192.168.0.3 &
    docker exec daq-faux-3 ping -c 3 192.168.0.1 &
    docker exec daq-faux-3 ping -c 3 192.168.0.2 &
    sleep 3

    test_pair 1 2
    test_pair 1 3
    test_pair 2 1
    test_pair 2 3
    test_pair 3 1
    test_pair 3 2

    echo Starting TCP probes...
    docker exec daq-faux-1 nc -w 1 192.168.0.2 23 2>&1 | tee -a $TEST_RESULTS
    docker exec daq-faux-1 nc -w 1 192.168.0.2 443 2>&1 | tee -a $TEST_RESULTS

    echo Waiting for pair tests to complete...
    start_time=$(date +%s)
    wait
    end_time=$(date +%s)
    echo Waited $((end_time - start_time))s.

    bcount6=$(tcpdump -en -r $t2sw1p6_pcap | wc -l) 2>/dev/null
    bcount7=$(tcpdump -en -r $t2sw1p7_pcap | wc -l) 2>/dev/null
    bcount_total=$((bcount6 + bcount7))
    echo pcap $mode count is $bcount6 $bcount7 $bcount_total
    echo pcap sane $((bcount_total > 100)) $((bcount_total < 130)) | tee -a $TEST_RESULTS
    echo pcap t2sw1p6
    tcpdump -en -c 20 -r $t2sw1p6_pcap
    echo pcap t2sw1p7
    tcpdump -en -c 200 -r $t2sw1p7_pcap
    echo pcap end

    telnet6=$(tcpdump -en -r $t2sw1p6_pcap vlan and port 23 | wc -l) 2>/dev/null
    https6=$(tcpdump -en -r $t2sw1p6_pcap vlan and port 443 | wc -l) 2>/dev/null
    telnet7=$(tcpdump -en -r $t2sw1p7_pcap vlan and port 23 | wc -l) 2>/dev/null
    https7=$(tcpdump -en -r $t2sw1p7_pcap vlan and port 443 | wc -l) 2>/dev/null
    echo $mode telnet $((telnet6 + telnet)) https $((https6 + https7)) | tee -a $TEST_RESULTS

    cat $nodes_dir/* | tee -a $TEST_RESULTS

    echo Done with stack test $mode. | tee -a $TEST_RESULTS
}

echo Stacking Tests >> $TEST_RESULTS
test_stack nobond
# https://github.com/faucetsdn/faucet/issues/2864
#test_stack bond

echo Cleanup bridges...
for bridge in corp t1sw1 t1sw2 t2sw1 t2sw2; do
    echo Cleaning $bridge...
    sudo timeout 1m ovs-vsctl del-br $bridge
done

echo Done with cleanup. Goodby.
