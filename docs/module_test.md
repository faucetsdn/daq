# Module Test

Docker test modules can be tested individually to validate basic functionality.

## Basic Setup

The requisite test containers need to be available, and
```$ cp misc/system_all.conf local/system.conf```

## Test Execution

<pre>
~/daq$ bin/test_module tls
Activating venv
Loading config from local/system.conf into inst/config/system.conf
Enabling target faux
Enabling target test_tls
Skipping non-enabled daqf/aardvark
Skipping non-enabled daqf/default
Skipping non-enabled daqf/faucet
Build docker/Dockerfile.faux into daqf/faux, log to build/docker_build.faux...
Skipping non-enabled daqf/gauge
Skipping non-enabled daqf/networking
Skipping non-enabled daqf/switch
Skipping non-enabled daqf/test_bacnet
Skipping non-enabled daqf/test_fail
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

Module test results:
RESULT skip security.tls.v3
RESULT skip security.x509
</pre>

## Development Target

In order to test various conditions, the faux container needs to be instrumented to support the
necessary test cases.

E.g., to test the tls module against an expired certificate, the system can be run like

```bin/test_modules tls expiredtls```

(requiring, of course, that the faux module is set up appropriately).

## Continous Testing

Continuous testing should be setup in the `testing/test_modules.sh` script. Adding an entry in
there, and updating `testing/test_modules.out` to match, will ensure that the container is
tested appropriately.
