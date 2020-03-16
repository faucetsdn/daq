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
EOF

DAQ_TARGETS=faux bin/docker_build build-all

cat $TEST_LIST | while read module args; do
    if ! docker inspect daqf/test_$module:latest > /dev/null; then
	DAQ_TARGETS=test_$module bin/docker_build build-all
    fi
    echo
    echo Testing $module $args | tee -a $TEST_RESULTS
    if bin/test_module -n $module $args; then
        cat inst/module/$module/tmp/result_lines.txt >> $TEST_RESULTS
    else
        echo Module execution failed. >> $TEST_RESULTS
    fi
done

echo
echo Testing complete. | tee -a $TEST_RESULTS
