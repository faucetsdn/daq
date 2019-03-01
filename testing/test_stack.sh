#!/bin/bash

source testing/test_preamble.sh

out_dir=out/daq-test_stack
rm -rf $out_dir

t2sw1p6_pcap=$out_dir/t2sw1-eth6.pcap
t2sw1p7_pcap=$out_dir/t2sw1-eth7.pcap
nodes_dir=$out_dir/nodes

mkdir -p $out_dir $nodes_dir

setup_delay=60
cap_length=20

echo Generator tests | tee -a $TEST_RESULTS
rm -rf out/topology
normalize_base=topology/un-moon/un-moon-ctr0g-1-1/
bin/generate_topology raw_topo=$normalize_base topo_dir=out/topology/normalized
diff -r out/topology/normalized $normalize_base | tee -a $TEST_RESULTS

sites=$(cd topology; ls -d *)
mkdir -p out/topology/generated
for site in $sites; do
    if [ ! -d topology/$site ]; then
        continue;
    fi
    bin/generate_topology site_config=topology/$site/site_config.json topo_dir=out/topology/generated/$site
done
diff -r out/topology/generated topology/ | tee -a $TEST_RESULTS

echo Stacking Tests >> $TEST_RESULTS

bin/setup_stack || exit 1

echo Configured bridges:
bridges=$(ovs-vsctl list-br | sort)
for bridge in $bridges; do
    echo
    echo OVS bridge $bridge
    ovs-ofctl show $bridge
done

echo
echo Waiting $setup_delay sec for stack to settle | tee -a $TEST_RESULTS
sleep $setup_delay

function test_pair {
    src=$1
    dst=$2

    host=daq-faux-$src
    out_file=$nodes_dir/$host-$dst
    cmd="ping -c 10 192.168.0.$dst"
    echo $host: $cmd
    echo -n $host: $cmd\ > $out_file
    docker exec $host $cmd | fgrep time= | fgrep -v DUP | wc -l >> $out_file 2>/dev/null &
}

echo Capturing pcap to $t2sw1p6_pcap for $cap_length seconds...
timeout $cap_length tcpdump -eni t2sw1-eth6 -w $t2sw1p6_pcap &
timeout $cap_length tcpdump -eni t2sw1-eth7 -w $t2sw1p7_pcap &
sleep 5

test_pair 1 2
test_pair 1 3
test_pair 2 1
test_pair 2 3
test_pair 3 1
test_pair 3 2

docker exec daq-faux-1 nc -w 1 192.168.0.2 23 2>&1 | tee -a $TEST_RESULTS
docker exec daq-faux-1 nc -w 1 192.168.0.2 443 2>&1 | tee -a $TEST_RESULTS

echo Waiting for pair tests to complete...
start_time=$(date +%s)
wait
end_time=$(date +%s)
echo Waited $((end_time - start_time))s.

bcount6=$(tcpdump -en -r $t2sw1p6_pcap | wc -l) 2>/dev/null
bcount7=$(tcpdump -en -r $t2sw1p7_pcap | wc -l) 2>/dev/null
echo pcap count is $bcount6 $bcount7
echo pcap sane $((bcount6 > 2)) $((bcount6 < 16)) $((bcount7 > 90)) $((bcount7 < 120)) | tee -a $TEST_RESULTS
echo pcap t2sw1p6
tcpdump -en -c 20 -r $t2sw1p6_pcap
echo pcap t2sw1p7
tcpdump -en -c 200 -r $t2sw1p7_pcap
echo pcap end

telnet6=$(tcpdump -en -r $t2sw1p6_pcap vlan and port 23 | wc -l) 2>/dev/null
https6=$(tcpdump -en -r $t2sw1p6_pcap vlan and port 443 | wc -l) 2>/dev/null
telnet7=$(tcpdump -en -r $t2sw1p7_pcap vlan and port 23 | wc -l) 2>/dev/null
https7=$(tcpdump -en -r $t2sw1p7_pcap vlan and port 443 | wc -l) 2>/dev/null
echo telnet $telnet6 $telnet7 https $https6 $https7 | tee -a $TEST_RESULTS

cat $nodes_dir/* | tee -a $TEST_RESULTS

echo Faucet logs
more inst/faucet/*/faucet.log | cat
echo nz-kiwi-ctr1
docker logs nz-kiwi-ctr1 | tail
echo nz-kiwi-ctr2
docker logs nz-kiwi-ctr2 | tail

echo Done with stack test. | tee -a $TEST_RESULTS

echo Cleanup bridges...
sudo ovs-vsctl del-br corp
sudo ovs-vsctl del-br t1sw1
sudo ovs-vsctl del-br t1sw2
sudo ovs-vsctl del-br t2sw1
sudo ovs-vsctl del-br t2sw2

echo Done with cleanup. Goodby.
