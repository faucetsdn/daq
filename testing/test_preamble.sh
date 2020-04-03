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
echo Writing test results to $TEST_RESULTS and $GCP_RESULTS
echo Running $0 > $TEST_RESULTS
echo Running $0 > $GCP_RESULTS

if [ -n "$GCP_SERVICE_ACCOUNT" ]; then
  echo GCP_SERVICE_ACCOUNT has been deprecated. | tee -a $TEST_RESULTS
  echo Please reconfigure as per docs/integration_testing.md
fi

lsb_release -a

mkdir -p inst/config
cred_file=inst/config/gcp_service_account.json

if [ -f $cred_file ]; then
  echo Found previously configured $cred_file
elif [ -n "$GCP_BASE64_CRED" ]; then
  echo Decoding GCP_BASE64_CRED to $cred_file
  echo base64 wc: `echo "$GCP_BASE64_CRED" | wc`
  echo "$GCP_BASE64_CRED" | base64 -d > $cred_file
else
  echo No GCP credentials found.
fi

if [ -f $cred_file ]; then
  echo GCP service account is `jq .client_email $cred_file`
fi

# Remove things that will always (probably) change - like DAQ version/timestamps/IPs
# from comparison

function redact {
    sed -E -e "s/ \{1,\}$//" \
        -e 's/\s*%%.*//' \
        -e 's/[0-9]{4}-.*T.*Z/XXX/' \
        -e 's/[a-zA-Z]{3} [a-zA-Z]{3}\s+[0-9]{1,2} [0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2} [0-9]{4}/XXX/' \
        -e 's/[0-9]{4}-(0|1)[0-9]-(0|1|2|3)[0-9] [0-9]{2}:[0-9]{2}:[0-9]{2}\+00:00/XXX/g' \
        -e 's/[0-9]+\.[0-9]{2} seconds/XXX/' \
        -e 's/DAQ version.*//' \
        -e 's/\b(?:\d{1,3}\.){3}\d{1,3}\b/XXX/'
        -e 's/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/X.X.X.X/'
}
