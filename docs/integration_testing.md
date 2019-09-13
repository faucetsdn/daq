# Integration Testing

DAQ currently uses Travis CI for integration testing: https://travis-ci.org/

## Configuration

### GCP Credential

To run cloud-based tests, setup the Travis `GCP_BASE64_CRED` env variable with a `base64` encoded
service account key for your project. It's recommended to use a dedicated key with a nice name
like `daq-travis`, but not required. Encode the key value as per below, and cut/paste the
resulting string into the Travis settings page for a `GCP_BASE64_CRED` varaible.
Note the `-w 0` option is required for proper parsing/formatting, as there can't be any
newlines in the copied string.

<code>
$ <b>base64 -w 0 local/gcp_service_account.json</b>
ewoICJ1eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAiYm9zLWRhcS10ZXN0aW5nIiwKICAicHJpd
&hellip;
iOiAiaHR0cHM6Ly93LWRhcS10ZXN0aW5nLmlhbS5nc2VydmljZWFjY291bnQuY29tIgp9Cg==
</code>

### Is my Travis set up correctly?

If Travis is set up correctly, you should see messages at the beginning of the log file:
```
Setting environment variables from repository settings
$ export DOCKER_USERNAME=[secure]
$ export DOCKER_PASSWORD=[secure]
$ export GCP_BASE64_CRED=[secure]
```

Further down there would be more details about the cred itself:
```
Running test script testing/test_aux.sh
Writing test results to inst/test_aux.out and inst/test_aux.gcp
Decoding GCP_BASE64_CRED to inst/config/gcp_service_account.json
base64 wc: 1 1 3097
GCP service account is "daq-travis@daq-testing.iam.gserviceaccount.com"
```

If the `3097` character count is wildly off, then likely something went wrong with the newlines.

### Travis Build For "External" Pull Requests

Travis will not use encrypted environment variables when testing against pull requests
from foreign github repositories, even if you've forked from another repository that you
have full control of via Github. Travis authorization != Github authorization, even if
you sign into Travis using Github! This is as it should be b/c security. see the following
for more info:

- https://docs.travis-ci.com/user/environment-variables/#defining-variables-in-repository-settings
- https://docs.travis-ci.com/user/pull-requests/#pull-requests-and-security-restrictions

If your test is failing from a PR, you'll see something like in a similar log location:

```
Encrypted environment variables have been removed for security reasons.
See https://docs.travis-ci.com/user/pull-requests/#pull-requests-and-security-restrictions
Setting environment variables from .travis.yml
$ export DOCKER_STARTUP_TIMEOUT_MS=60000
$ export DAQ_TEST=aux
```

### Other Travis Caveats

Take note the URL in your browser's address bar when running Travis. You might be on either
<code>travis-ci<b>.com</b></code> or <code>travis-ci<b>.org</b></code>. Any particular setup
may end up across both sites for undertermined reasons. Please consult with your browser's
exact URL for more clarity.
