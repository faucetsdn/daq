#!/bin/bash

source testing/test_preamble.sh

echo Base Tests >> $TEST_RESULTS

mkdir -p local
echo 'include=../config/system/all.conf' > local/system.conf

if [ -d venv ]; then
    echo Activating venv
    source venv/bin/activate
fi

TLS_CONFIG_DIR=inst/modules/tls/config
echo Resolve module config to $TLS_CONFIG_DIR
mkdir -p $TLS_CONFIG_DIR
python3 daq/configurator.py --json \
    resources/test_site/site_config.json > $TLS_CONFIG_DIR/module_config.json

TEST_LIST=/tmp/module_tests.txt
cat > $TEST_LIST <<EOF
tls alt
tls alt tls
tls alt expiredtls
ssh
ssh ssh
ssh sshv1
EOF

DAQ_TARGETS=aardvark,aardvark2,faux1,faux2 cmd/build missing inline

cat $TEST_LIST | while read module args; do
    if ! docker inspect daqf/test_$module:latest > /dev/null; then
	DAQ_TARGETS=test_$module cmd/build missing
    fi
    echo
    echo Testing $module $args | tee -a $TEST_RESULTS
    if bin/test_module -n $module $args; then
        fgrep RESULT inst/modules/$module/run/tmp/report.txt >> $TEST_RESULTS
    else
        echo Module $module execution failed. >> $TEST_RESULTS
    fi
done

echo
echo Testing complete. | tee -a $TEST_RESULTS
