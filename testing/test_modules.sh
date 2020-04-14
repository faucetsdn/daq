#!/bin/bash

source testing/test_preamble.sh

echo Base Tests >> $TEST_RESULTS

mkdir -p local
cp misc/system_all.conf local/system.conf

TEST_LIST=/tmp/module_tests.txt

cat > $TEST_LIST <<EOF
ping
tls
tls tls
tls expiredtls
tls alt tls
EOF

DAQ_TARGETS=faux1,faux2 bin/docker_build force

mkdir -p inst/modules/ping/config
echo '{"static_ip": "10.20.0.5"}' > inst/modules/ping/config/module_config.json

cat $TEST_LIST | while read module args; do
    if ! docker inspect daqf/test_$module:latest > /dev/null; then
	DAQ_TARGETS=test_$module bin/docker_build force
    fi
    echo
    echo Testing $module $args | tee -a $TEST_RESULTS
    if bin/test_module -n $module $args; then
        cat inst/modules/$module/run/tmp/result_lines.txt >> $TEST_RESULTS
    else
        echo Module $module execution failed. >> $TEST_RESULTS
    fi
done

echo
echo Testing complete. | tee -a $TEST_RESULTS
