# Adding a Runtime Test

The testing system DAQ uses is based on Docker containers. General familiarity with Docker is
assumed, as specific details are out of scope for this documentation. There are two steps
for testing: building the tests, and running them.

Test build configuration is controlled through the configuration parameter `host_tests`,
which defaults to `misc/host_tests.conf`. That file provides directives used to build tests
and specify which ones are available at runtime. Explicitly setting this value (e.g. to a
local file in the `local/` directory) can be used to customize base behavior. Once set,
both the `cmd/build` and `cmd/run` processes will pick it up.

The `misc/host_tests.conf` specifies the baseline set of tests that is used for basic regression
integration testing. `misc/all_tests.conf` is used to represent all of the tests available
to the system: more comprehensive, but slower to build and run.

Test _subsets_ should have a simple name that describes the rough idea of the group. Individual
test _modules_ are encapsulated in Dockerfiles that should have the name `Dockerfile.test_XXX`
where `XXX` represents the name of the individual test module. Generally best practice is to
follow the example set by the `subset/switcher` group of tests when adding a new subset.

## Example Test Setups

The _switcher_ test is configured in the `misc/all_tests.conf` file. To add a new test, there
should be a parallel structure, starting with a `build.conf` entry pointing to the new test
specification.

An example `flakey` test is included as a tutorial primer. To configure, do the following stems
(assuming a clean starting point):
* `mkdir -p local/docker` -- Make local directories.
* `cp misc/local_tests.conf local/` -- Copy the example test configuraiton file.
* `cp misc/Dockerfile.test_flaky local/docker/` -- Copy the example Docker file to build directory.
* `cp misc/system_base.conf local/system.conf` -- Create local version of system.conf file.
* `echo host_tests=local/local_tests.conf >> local/system.conf` -- Set tests configuration.

This, of course, only works for local development when using the `local_tests.conf` config. To
formalize a test and include it in the overal system build it should be included in
`misc/all_tests.conf`.

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

## Dynamic Configuration

The dynamic configuration of a test (if it is actually executed or is skipped completely),
is controller through the `module_config.json` file associated with the specific site install.
See `misc/module_config.json` for an example of what this looks like. Without this entry,
the test will be included into the runtime set of modules but not actually executed. The
execution behavior can be altered at runtime (through the web UI).

## Test Development

TODO: write note about hold_tests and test development
