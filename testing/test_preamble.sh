if [ `whoami` != 'root' ]; then
    echo Need to run as root.
    exit -1
fi

TEST_RESULTS=${TEST_RESULTS:-/tmp/test_results.out}
echo Writing test results to $TEST_RESULTS
echo Running $0 > $TEST_RESULTS
