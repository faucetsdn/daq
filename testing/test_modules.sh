#!/bin/bash

source testing/test_preamble.sh

echo Base Tests >> $TEST_RESULTS

bin/test_module ping
cat inst/module/ping/tmp/result_lines.txt >> $TEST_RESULTS

bin/test_module tls && \
    cat inst/module/tls/tmp/result_lines.txt >> $TEST_RESULTS
bin/test_module tls tls && \
    cat inst/module/tls/tmp/result_lines.txt >> $TEST_RESULTS
bin/test_module tls expiredtls && \
    cat inst/module/tls/tmp/result_lines.txt >> $TEST_RESULTS
