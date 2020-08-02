# Module Test

Docker test modules can be tested individually to validate basic functionality. The `test_module`
script sets up a basic network, faux container, and then runs a test module appropriately
configured. It should work properly for the majority of situations, but will not work for all cases.

## Basic Setup

In order to find the appropriate containers, the system needs to be configured such that the build
path has access to the module in question. Typically, this can be configured using:
<pre>$ cp config/system/all.conf local/system.conf</pre>
A new module can/should be enabled by
including it in the config/system/all.conf file. If the target module is not available on the path,
the build will fail:
<pre>Could not find specified test module to build: test_tls</pre>

## Test Execution

A test can be executed using the `test_module` command, which accepts the module name (e.g. `tls`)
and optional faux arguments to test against. The `-n` option can be given before the test name to
skip the build step.

<pre>
~/daq$ bin/test_module tls
Activating venv
Loading config from local/system.conf into inst/config/system.conf
Enabling target faux
Enabling target test_tls
Skipping non-enabled daqf/aardvark
&hellip;
Skipping non-enabled daqf/test_bacext
Skipping non-enabled daqf/test_password
Build subset/security/Dockerfile.test_tls into daqf/test_tls, log to build/docker_build.test_tls...
Skipping non-enabled daqf/test_udmi
Configuring OVS bridge daq-bridge-tls
Activating venv
&hellip;
%%%%%%%%%%%%%% Running module command ./test_tls %%%%%%%%%%%%%%%
report:IOException unable to connect to server.
RESULT skip security.tls.v3
RESULT skip security.x509

getCertificate IOException:Connection refused (Connection refused)
Certificate read failed
--------------------
Collecting TLS cert from target address %% 10.20.0.5
IOException unable to connect to server.

Killed containers daq-tls daq-faux-tls

echo %%%%%%%%%%%%%% Module test results: test_tls %%%%%%%%%%%%%%%
RESULT skip security.tls.v3
RESULT skip security.x509
</pre>

## Test target faux device options.

Arguments to the test command specify different faux target options to test against to verify
correct operation in different scenarios. The required faux behaviors will of course need to be
implemented along with test module behavior.

<pre>
~/daq$ bin/test_module tls
&hellip;
RESULT skip security.x509
</pre>

<pre>
~/daq$ bin/test_module -n tls tls
&hellip;
RESULT pass security.x509
</pre>

<pre>
~/daq$ bin/test_module -n tls expiredtls
&hellip;
RESULT fail security.x509
</pre>

## Continous Testing

Continuous testing of module-specific builds is handled through the `testing/test_modules.sh`
script (as invoked by [Github actions](https://github.com/faucetsdn/daq/actions)). Execution results are compared against the
`testing/test_modules.out` file. To add a new test, add a few lines to the top of the test script
and expected results to the output file. Every test module is required to be continously tested
somewhere, either as part of `test_modules.sh` or elsewhere.
