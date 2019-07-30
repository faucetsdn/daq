# Integration Testing

DAQ currently uses Travis CI for integration testing: https://travis-ci.org/

## Configuration

### GCP

If you're running cloud tests using pubber, Travis will need to be able to connect to your GCP account via the service account you've set up.  

You'll need to add another environment variable to Travis for this to work: 

- GCP_SERVICE_ACCOUNT

This variable is an string of your GCP account credentials file linked to the service account **with all spaces removed surrounded by single quotes**. If you've set everything up correctly, the json file you downloaded when you created the service account should be in your `local/` directory.

There are infinite ways to stringify JSON Use something like https://www.freeformatter.com/json-escape.html to convert your json object to a string, write a script to do it yourself, or use JSON.stringify in your browser JavaScript console.

Your new JSON string will look something like the below. Remember to *enclose the entire thing with single quotes*

```
'{"type":"service_account","project_id":"<here be a project id>","private_key_id":"<here be a private key>","private_key":"-----BEGINPRIVATEKEY-----\n<here be a key>\n-----ENDPRIVATEKEY-----\n","client_email":"<here be a sercret email>","client_id":"<here be a client id>","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"<here be another secret>"}'
```

#### YOUR TRAVIS BUILD MAY ALWAYS FAIL! Unless...

**Note** that, by default, Travis will not use encrypted environment variables when testing against pull requests from foreign github repositories, even if you've forked from another repository that you have full control of via Github. Travis authorization != Github authorization, even if you sign into Travis using Github! This is as it should be.

see the following for more info:

- https://docs.travis-ci.com/user/environment-variables/#defining-variables-in-repository-settings
- https://docs.travis-ci.com/user/pull-requests/#pull-requests-and-security-restrictions 

We're working on this...

#### Other Travis caveats

Take note the URL in your browser's address bar when running Travis. You might be on either:

- travis-ci **.com** (this is where the **"build"** step happens)
- travis-ci **.org** (this is where the **"ci"** step happens)

<img width="800" alt="Screenshot 2019-07-03 at 19 26 42" src="https://user-images.githubusercontent.com/5684825/60616075-962c0c80-9dc8-11e9-9e99-2b649dc23661.png">


There seem to be multiple places to add environment variables depending on which TLD you find yourself in. For personal Github accounts, there seems to be both **.com** _and_ **.org** addresses. For organizational Github accounts, only **.org** seems to be available.


#### Is my Travis set up correctly?

If Travis is set up correctly, you should see something like:

```
Setting environment variables from repository settings
$ export DOCKER_USERNAME=[secure]
$ export DOCKER_PASSWORD=[secure]
$ export GCP_SERVICE_ACCOUNT=[secure]
```

At the start of your Travis test log.

If your test is failing from a PR, you'll see something like in a similar log location:

```
Encrypted environment variables have been removed for security reasons.
See https://docs.travis-ci.com/user/pull-requests/#pull-requests-and-security-restrictions
Setting environment variables from .travis.yml
$ export DOCKER_STARTUP_TIMEOUT_MS=60000
$ export DAQ_TEST=aux
```
