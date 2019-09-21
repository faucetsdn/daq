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
follow the example set by the `subset/switches` group of tests when adding a new subset.

## Example Test Setups

The _switches_ test is configured in the `misc/all_tests.conf` file. To add a new test, there
should be a parallel structure, starting with a `build.conf` entry pointing to the new test
specification.

An example `flaky` test is included as a tutorial primer. To configure, do the following steps
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
is controlled through the `module_config.json` file associated with the specific site install.
See `misc/module_config.json` for an example of what this looks like. Without this entry,
the test will be included into the runtime set of modules but not actually executed. The
execution behavior can be altered at runtime (through the web user interface).

## Test Runtime Data

Runtime information is available to a test module (Docker container) in several
different places that are dynamically mapped into the system at runtime:
* `/tmp`: General information about a specific test run, saved after completion (not really `tmp` now is it?).
* `/scans`: Network scan of device traffic when the system is first starting up.
  * `startup.pcap`: Everything before a DHCP address is properly assigned.
  * `monitor.pcap`: Everything after DHCP, but before actual tests.
* `/config/inst`: Global DAQ instance configuration from `inst/config`. Includes processed system.conf settings.
* `/config/device`: Device-specific customizations from `{site_path}/mac_addrs/{device_mac}/aux/`.
* `/config/port`: Switch-port customizations from `inst/runtime_conf/port-##/`.
* `/config/type`: Device-type customizations from `{site_path}/device_types/{device_type}/aux/`.
  * See `misc/test_site/mac_addrs/9a02571e8f01/module_config.json` as an example of specifying device type.
  * See `misc/test_site/device_types/rocket/` for an example device type.
  * See `qualification/*` for more detailed examples of test configuration files.

## Test Development Philosophy

DAQ is an extensible framework for running arbitrary tests. Because tests are run inside Docker containers, the language or environment you choose to write device tests is unimportant. If it will run in Docker, DAQ can run it!

However, with great flexibility comes great responsibility. 
Tests should:

- Test _one_ thing well
- Include an integration test for Travis CI
- Adhere to the Google style guide of your chosen language: https://google.github.io/styleguide/
- Have the smallest amount of code possible for the greatest utility for the framework. Keep docker images lean!
- Not add things like the following to the repository:
    - Favourite settings for your IDE
    - Compiled binaries
    - Deployment keys
    - Secrets
    - References to companies and device manufacturers
- Include the test name and a description of the test in the report output
- Include an informative line in the summary table

Integration tests don't need to be tedious and, if you're developing one test and seeing a consistent failure on Travis CI, isolate your problem and run _just that part_ of the integration test both locally and on Travis CI.

The pass/fail state of an integration test corresponds to the result of a `diff` between expected and actual device report output. You can follow the steps in the _Integration Testing Workflow_ section below to mimic the exact process that Travis CI follows. Or, if your local machine builds Docker images slowly, simply modify the test_*.out by hand, amending it to what your report should look like. Then, see if Travis CI agrees.

Similarly, if you're writing one test and running it within DAQ locally, run _only the test you're developing_. Try not to bloat your precious development hours by waiting for tests to run that you don't care about. Building unnecessary tests is a very efficient time sink.

## Integration Testing Workflow 

The integration testing workflow involves modifying the test_x.out file to what is expected for the test to output.

This can be accomplished by running test_x.sh file multiple times and copying it over to the out file, according to the following procedure.
All of the commands in these steps are run as the root user by typing "sudo -i" in the terminal.

1. Run daq from the base directory using the command `cmd/run -s`
2. Commit to GitHub to sync local codebase with remote codebase
3. Run `testing_x.sh` 
4. Copy the file `inst/reports/report_9a02571e8f01_xxxx-xx-xxTxxxxxx+xxxx.md` to `docs/device_report.md`
5. Commit to GitHub to sync local codebase with remote codebase
6. Run `testing/test_x.sh` 
7. Copy `out/test_x.out` to `testing/test_x.out` 
8. Run `testing/test_x.sh` to check the integration tests now execute successfully in the local machine.
9. Commit to GitHub to sync local codebase with remote codebase and to trigger the final Travis CI tests
10. Test should now pass the Travis CI integration tests.

TODO: write note about hold_tests 
