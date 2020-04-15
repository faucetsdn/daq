#!/bin/bash

out_dir=$1
mkdir -p $out_dir

ip addr > $out_dir/ip_addr.txt
route -n > $out_dir/route.txt
arp -n > $out_dir/arp.txt
ovs-vsctl show > ovs_vsctl.txt

function dump {
    ovs-ofctl show $1 > $out_dir/$1.ofctl
    ovs-ofctl dump-flows $1 > $out_dir/$1.flows
}

dump pri
dump sec

#cp inst/faucet.log $1/
cp inst/faucet.yaml inst/dp_ports_acl.yaml inst/port_acls/*.yaml $1/
