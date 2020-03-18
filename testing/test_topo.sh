#!/bin/bash

source testing/test_preamble.sh

echo Topology Tests >> $TEST_RESULTS

# Test the mudacl config and the test_schema to make sure they
# make sense for tests that use them

echo mudacl tests | tee -a $TEST_RESULTS
mudacl/bin/test.sh
echo Mudacl exit code $? | tee -a $TEST_RESULTS
validator/bin/test_schema
echo Validator exit code $? | tee -a $TEST_RESULTS

bacnet_file=/tmp/bacnet_result.txt
socket_file=/tmp/socket_result.txt

MAC_BASE=9a:02:57:1e:8f

source testing/test_utils.sh

generate open 3
cmd/build
check_socket 01 02 1 1
check_socket 02 01 1 1
check_bacnet 01 02 1 1 1 1
check_bacnet 02 03 1 1 1 1
check_bacnet 03 01 1 1 1 1
run_test 3

generate minimal 3
check_bacnet 01 02 1 1 1 1
check_bacnet 02 03 0 1 1 1
check_bacnet 03 01 1 1 1 1
run_test 3

generate commissioning 4
check_socket 01 04 0 0
check_socket 01 02 0 0
check_socket 04 01 0 0
check_bacnet 01 02 1 1 1 1
check_bacnet 01 04 1 1 1 1
check_bacnet 02 03 0 1 1 1
check_bacnet 02 04 1 1 1 1
check_bacnet 03 01 1 1 1 1
run_test 4

echo %%%% ovs_ofctl show
cat ofctl_show_pri.txt
cat ofctl_show_sec.txt
echo %%%% ip link
cat ip_link.txt
echo %%%%

echo Done with tests | tee -a $TEST_RESULTS
