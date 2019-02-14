#!/bin/bash

out_dir=$1
mkdir -p $out_dir

ovs-vsctl show

function dump {
    ovs-ofctl show $1 > $out_dir/$1.ofctl
    ovs-ofctl dump-flows $1 > $out_dir/$1.flows
}

dump ctrl-br
dump ext-ovs
dump pri
dump sec

echo

ip link

