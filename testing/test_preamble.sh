if [ `whoami` != 'root' ]; then
    echo Need to run as root.
    exit -1
fi

mkdir -p out
test_script=${0##*/}
def_name=${test_script%.sh}.out
gcp_name=${test_script%.sh}.gcp
TEST_RESULTS=${TEST_RESULTS:-out/$def_name}
GCP_RESULTS=${GCP_RESULTS:-out/$gcp_name}
GCP_FILE=inst/config/gcp_service_account.json

echo Writing test results to $TEST_RESULTS and $GCP_RESULTS
echo Running $0 > $TEST_RESULTS
echo Running $0 > $GCP_RESULTS

if [ -n "$GCP_SERVICE_ACCOUNT" ]; then
  echo GCP_SERVICE_ACCOUNT has been deprecated. | tee -a $TEST_RESULTS
  echo Please reconfigure as per docs/integration_testing.md
fi

lsb_release -a

mkdir -p inst/config
gcp_cred=

if [ -f $GCP_FILE ]; then
  gcp_cred=$GCP_FILE
  echo Found previously configured $gcp_cred
elif [ -n "$GCP_BASE64_CRED" ]; then
  gcp_cred=$GCP_FILE
  echo Decoding GCP_BASE64_CRED to $gcp_cred
  echo base64 wc: `echo "$GCP_BASE64_CRED" | wc`
  echo "$GCP_BASE64_CRED" | base64 -d > $gcp_cred
else
  echo No GCP credentials found.
fi

if [ -f "$gcp_cred" ]; then
  echo GCP service account is `jq .client_email $gcp_cred`
fi

function kill_children {
    pkill -P $$
}

trap kill_children EXIT

# Remove things that will always (probably) change - like DAQ version/timestamps/IPs
# from comparison

function redact {
    sed -E -e "s/ \{1,\}$//" \
        -e 's/\s*%%.*//' \
        -e 's/[0-9]{4}-.*T.*Z/XXX/' \
        -e 's/[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2} [A-Z]{3}/XXX/' \
        -e 's/[a-zA-Z]{3} [a-zA-Z]{3}\s+[0-9]{1,2} [0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2} [0-9]{4}/XXX/' \
        -e 's/[0-9]{4}-(0|1)[0-9]-(0|1|2|3)[0-9] [0-9]{2}:[0-9]{2}:[0-9]{2}(\+00:00)?/XXX/g' \
        -e 's/[0-9]+\.[0-9]{2} seconds/XXX/' \
        -e 's/0\.[0-9]+s latency/XXX/' \
        -e 's/open\|filtered/closed/' \
        -e 's/DAQ version.*//' \
        -e 's/Not shown: .* ports//' \
        -e 's/([0-9]{1,3}\.){3}[0-9]{1,3}/X.X.X.X/'
}

function monitor_log {
    logmessage=$1
    runcommand=$2
    rm -f inst/cmdrun.log
    while true; do
        sleep 1
        found=$(cat inst/cmdrun.log 2>/dev/null | grep "$logmessage")
        if [ -n "$found" ]; then
            echo found $found
            eval $runcommand
            break
        fi
        test_done=$(cat $TEST_RESULTS | grep "Done with tests")
        if [ -n "$test_done" ]; then
            break
        fi
    done &
}

function monitor_marker {
    MARKER=$1
    RUNCMD=$2
    rm -f $MARKER
    (
        while [ ! -f $MARKER ]; do
            test_done=$(cat $TEST_RESULTS | grep "Done with tests")
            if [ -n "$test_done" ]; then
                break
            fi
            echo test_aux.sh waiting for $MARKER
            sleep 60
        done
        echo Found $MARKER, executing $RUNCMD
        $RUNCMD
    ) &
}
