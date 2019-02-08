if [ `whoami` != 'root' ]; then
    echo Need to run as root.
    exit -1
fi

mkdir -p out
test_script=${0##*/}
def_name=${test_script%.sh}.out
TEST_RESULTS=${TEST_RESULTS:-out/$def_name}
echo Writing test results to $TEST_RESULTS
echo Running $0 > $TEST_RESULTS
