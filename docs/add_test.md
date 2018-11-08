# Adding a Runtime Test

The testing system DAQ uses is based on Docker containers. General familiarity with Docker is
assumed, as specific details are out of scope for this documentation. There are two steps
for testing: building the tests, and running them.

Test configuration is controlled through the configuration parameter `host_tests`, which defaults
to `misc/host_tests.conf`. That file provides directives used to build and run tests appropriately.
Explicitly setting this value (e.g. to a local file in the `local/` directory) can be used to
customize base behavior. Once set, both the `cmd/build` and `cmd/run` processes will pick it up.

## Example Setup

An example `flakey` test is included as a tutorial primer. To configure, do the following stems
(assuming a clean starting point):
* `mkdir -p local/docker` -- Make local directories.
* `cp misc/local_tests.conf local/` -- Copy the example test configuraiton file.
* `cp misc/Dockerfile.test_flaky local/docker/` -- Copy the example Docker file to build directory.
* `cp misc/system.conf local/system.conf` -- Create local version of system.conf file.
* `echo host_tests=local/local_tests.conf >> local/system.conf` -- Set tests configuration.

## Component Build

To build all the tests, use the `cmd/build` script. This builds all the tests in indicated
directories, if they are configured to run or not. The output should be something like (novel
parts <b>in bold</b>):

<pre>
~/daq$ cmd/build 
Loading build configuration from local/system.conf
Including build files from docker
Including build files from <b>local/docker</b>
Build docker/Dockerfile.aardvark into daq/aardvark, log to build/docker_build.aardvark...
Build docker/Dockerfile.default into daq/default, log to build/docker_build.default...
&hellip;
Build docker/Dockerfile.test_pass into daq/test_pass, log to build/docker_build.test_pass...
Build docker/Dockerfile.test_ping into daq/test_ping, log to build/docker_build.test_ping...
Build <b>local/docker/Dockerfile.test_flaky</b> into daq/test_flaky, log to build/docker_build.test_flaky...
</pre>

## Runtime Execution

At runtime, behaviour should be as expected with a few changes. Note that the `flaky` test
is exactly that: flaky, so expect it to fail half the time!

<pre>
~/daq$ cmd/run
Loading config from local/system.conf
run_mode is local
&hellip;
INFO:gcp:No gcp_cred credential specified in config
INFO:runner:Reading test definition file <b>local/local_tests.conf</b>
INFO:runner:Reading test definition file misc/host_tests.conf
INFO:runner:<b>Configured with tests ['mudgee', 'flaky']</b>
INFO:network:Activating faucet topology...
INFO:topology:No device_specs file specified, skipping...
&hellip;
INFO:host:Target port 1 scan complete
INFO:host:Target port 1 monitor scan complete
INFO:docker:Target port 1 PASSED test mudgee
INFO:docker:Target port 1 <b>PASSED test flaky</b>
INFO:host:Target port 1 no more tests remaining
INFO:host:Finalizing report inst/report_9a02571e8f00_2018-11-06T21:20:51.txt
&hellip;
</pre>
