# Building DAQ

Building DAQ is only required if you are doing active development on DAQ itself (or using head-of
branch features); it will require installing more prerequisites that aren't indicated above.
In addition to some standard packages, it requires specific versions of <code>mininet</code>
and <code>FAUCET</code> that are tied to this specific build (but, you will have to manually
update them in the future).

## Major Steps

<code>$ <b>bin/clean_dev</b></code> # Clean up any previous development installs.

<code>$ <b>bin/setup_dev</b></code> # Setup of basic dev environment dependencies.

<code>$ <b>cmd/build</b></code> # Build internal docker images.

<code>$ <b>cmd/clean</b></code> # Clean up docker images that may be lingering.

Sadly, there's no easy way to know when you need to run what when, since they simply address
different dependencies.

To run in development mode (not a container), use <code>cmd/run <b>local</b> ...</code>,
or set `run_mode=local` in the `local/system.conf` file.

## Tests, Tests, and More Tests

In a whirlwind of flagrant appropriateness, the baseline for DAQ development is... testing. Specifically,
there is a suite of continuous integration tests that run on [Travis CI](https://travis-ci.com/faucetsdn/daq)
that puts the system through a barrage of tests to make sure all is good. Any PR submission will
require that these tests pass. It's recommended (but not required) that you set up Travis CI on
your personal development branch to test your commits in the full Travis CI environment before relying
on the automatic PR test mechanism.

The `.travis.yml` file contains the information for the tests themselves, primarily listed under the `matrix:`
subsection that shows all the various tested configurations. Note that this assumes a fully installed environment
(as setup with `bin/setup_daq`). From there, individual tests can be run locally by
appending `bin/test_daq` to a `sudo` line of shell environment settings, e.g. as taken from one matrix entry:
<pre>
~/daq$ <b>sudo DAQ_TEST=base bin/test_daq</b>
&hellip;
<em>or directly with:</em>
~/daq$ <b>sudo testing/test_base.sh</b>
&hellip;
</pre>

## Incremental Builds

The environment variable `DAQ_TARGETS` is a CSV-field that can be used to only build specific targets. E.g.
to just build the `ping` tests use the short form `DAQ_TARGETS=test_ping cmd_build`. Using a more sticky
exported varaible, for `ping` and `nmap`, would look something like:
<pre>
~/daq$ <b>export DAQ_TARGETS=test_ping,test_nmap</b>
~/daq$ <b>cmd/build</b>
Loading config from local/system.conf...
<b>Enabling target test_ping</b>
<b>Enabling target test_nmap</b>
Including tests from misc/host_tests.conf
Including build files from docker
&hellip;
Skipping non-enabled daq/test_mudgee
Skipping non-enabled daq/test_pass
<b>Build docker/Dockerfile.test_ping into daq/test_ping, log to build/docker_build.test_ping...</b>
Skipping non-enabled daq/test_brute
<b>Build subset/pentests/Dockerfile.test_nmap into daq/test_nmap, log to build/docker_build.test_nmap...</b>
Skipping non-enabled daq/test_switch
Updating .build_hash
~/daq$
</pre>

## Build Debugging

`cmd/run` and `cmd/build` have some internal checks that attempt to make sure the built Docker images are
current with the existing filesystem setup. This is only a hint and optimization. If there are consistent
messages about the build hash being out of date, and it's not clear why, then the folowing steps will help
clarify what file is changed that is triggering the warning.

<pre>
~/daq$ <b>cmd/run</b>
Loading config from local/system.conf
<b>Local build hash does not match, or not found.</b>
Please run cmd/build, or if you know what you're doing:
echo ab1a2dac87a9316676db74a16c5927cfd21b9976fcbf9850e42c5e5b7bdba5fe > .build_hash
~/daq$ <b>diff .build_built .build_files</b>
7d6
< 8c7daf2497ad5f35db5fb2ce340b5d47e42a10de  docker/Dockerfile.switch~
29,30d27
< 22b83fb943e92968bb29116c1fc93672c90139f6  misc/discover_config/port-01/ping_runtime.sh~
< 510742d89d5da3a171662597d95caffbb55788e7  misc/discover_config/port-02/monitor_filter.txt~
~/daq$ <b>cmd/build</b>
Loading config from local/system.conf...
Including build files from docker
Including build files from subset/pentests
Build docker/Dockerfile.aardvark into daq/aardvark, log to build/docker_build.aardvark...
Build docker/Dockerfile.default into daq/default, log to build/docker_build.default...
&hellip;
Build subset/pentests/Dockerfile.test_brute into daq/test_brute, log to build/docker_build.test_brute...
Build subset/pentests/Dockerfile.test_nmap into daq/test_nmap, log to build/docker_build.test_nmap...
Updating .build_hash
~/daq$ <b>cmd/run</b>
Loading config from local/system.conf
<b>Starting Mon Feb 11 08:40:12 PST 2019, run_mode is local</b>
&hellip;
</pre>

The file `.build_built` includes the hashes from the last time the system successfully completed
a `cmd/build` run, while `.build_files` contains the hashes after the most recent `cmd/run` hash mismatch.
The example `diff` above indicates that some files were deleted from the `docker/` and `misc/`
directories, triggering the rebuild requirement.
