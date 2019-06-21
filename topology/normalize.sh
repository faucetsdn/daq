#!/bin/bash -e

ROOT=$(dirname $0)/..
if [ ! -d "$1" ]; then
    echo $0 [topology dir]
    false
fi

TDIR=$(realpath $1)

$ROOT/bin/generate_topology raw_topo=$TDIR topo_dir=$TDIR

