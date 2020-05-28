#!/bin/bash

source testing/test_preamble.sh

rm -rf inst/tmp_site && mkdir -p inst/tmp_site
cp misc/report_template.md inst/tmp_site/

rm -f local/system.yaml local/system.conf

MARKER=inst/run-port-01/nodes/hold01/activate.log
monitor_marker $MARKER "sudo ip link set pri-eth1 down"

cmd/run -k -s site_path=inst/tmp_site
