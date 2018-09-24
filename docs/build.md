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

Sadly, there's no "easy" way to know when you need to run what when, since they simply address
different dependencies.

To run in development mode (not a container), use <code>cmd/run <b>local</b> ...</code>,
or set `run_mode=local` in the `local/system.conf` file.

## Tests, Tests, and More Tests

In a whirlwind fit of appropriateness, the baseline for DAQ development is... testing. Specifically,
there is a suite of continuous integration tests that run on [Travis CI](https://travis-ci.com/faucetsdn/daq)
that puts the system through a barrage of tests to make sure all is good. Any PR submission will
require that these tests pass. It's recommended (but not required) that you set up Travis CI on
your personal development branch to test your commits in the full Travis CI environment before relying
on the automatic PR test mechanism.

The `.travis.yml` file contains the information for the tests themselves, primarily listed under the `matrix:`
subsection that shows all the various tested configurations. Note that this assumes a fully installed and
_clean_ environment (e.g. no `local/system.conf` file). From there, individual tests can be run locally by
appending `bin/test_daq` to a line of shell environment settings, e.g. as taken from one matrix entry:<pre>
~/daq$ DAQ_CONF=misc/faucet_multi.yaml DAQ_MUD=true DAQ_VALIDATE=y DAQ_RUNS=10 bin/test_daq
</pre>
