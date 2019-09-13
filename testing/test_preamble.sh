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
