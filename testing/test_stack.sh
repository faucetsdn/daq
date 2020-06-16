#!/bin/bash

source testing/test_preamble.sh

out_dir=out/daq-test_stack
rm -rf $out_dir

t2sw1p47_pcap=$out_dir/t2sw1-eth47.pcap
t2sw1p48_pcap=$out_dir/t2sw1-eth48.pcap
nodes_dir=$out_dir/nodes

mkdir -p $out_dir $nodes_dir

ping_count=10
cap_length=$((ping_count + 20))

echo Generator tests | tee -a $TEST_RESULTS
rm -rf out/topology
bin/generate_topology raw_topo=topology/not-normal/nz-kiwi-ctr1 topo_dir=out/topology/normalized
#diff -r out/topology/normalized topology/nz-kiwi-ctr1/ | tee -a $TEST_RESULTS

sites=$(cd topology; ls -d *)
mkdir -p out/topology/generated
for site in $sites; do
    if [ ! -f topology/$site/site_config.json ]; then
        continue;
    fi
    bin/generate_topology site_config=topology/$site/site_config.json topo_dir=out/topology/generated/$site
done
#diff -r out/topology/generated topology/ | tee -a $TEST_RESULTS

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

    echo Capturing pcap to $t2sw1p47_pcap for $cap_length seconds...
    timeout $cap_length tcpdump -eni t2sw1-eth47 -w $t2sw1p47_pcap &
    timeout $cap_length tcpdump -eni t2sw1-eth48 -w $t2sw1p48_pcap &
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

    bcount47=$(tcpdump -en -r $t2sw1p47_pcap | wc -l) 2>/dev/null
    bcount48=$(tcpdump -en -r $t2sw1p48_pcap | wc -l) 2>/dev/null
    bcount_total=$((bcount47 + bcount48))
    echo pcap $mode count is $bcount47 $bcount48 $bcount_total
    echo pcap sane $((bcount_total > 100)) $((bcount_total < 220)) | tee -a $TEST_RESULTS
    echo pcap t2sw1p47
    tcpdump -en -c 20 -r $t2sw1p47_pcap
    echo pcap t2sw1p48
    tcpdump -en -c 20 -r $t2sw1p48_pcap
    echo pcap end

    telnet47=$(tcpdump -en -r $t2sw1p47_pcap vlan and port 23 | wc -l) 2>/dev/null
    https47=$(tcpdump -en -r $t2sw1p47_pcap vlan and port 443 | wc -l) 2>/dev/null
    telnet48=$(tcpdump -en -r $t2sw1p48_pcap vlan and port 23 | wc -l) 2>/dev/null
    https48=$(tcpdump -en -r $t2sw1p48_pcap vlan and port 443 | wc -l) 2>/dev/null
    echo $mode telnet $((telnet47 + telnet48)) https $((https47 + https48)) | tee -a $TEST_RESULTS

    cat $nodes_dir/* | tee -a $TEST_RESULTS

    echo Done with stack test $mode. | tee -a $TEST_RESULTS
}

echo Stacking Tests >> $TEST_RESULTS
#bin/net_clean
#test_stack nobond

bin/net_clean
test_stack bond

bin/net_clean

echo Done with cleanup. Goodbye.
