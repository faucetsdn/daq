# DAQ Developers Guide

## Testing Overview

In order to guarantee the integrity of the DAQ framework itself, a suite of
_integration tests_ is used that encompasses the core python code as well as general
execution of the main test modules. This is different than the _device tests_ which
are run against a target device. The main purpose of the integration is to catch
unintended consequences of any code change, and to make sure that existing code
doesn't break in unexpected ways.

One of the integration tests is the [module test](module_test.md), which lets you
test an individual Docker module without running the entire test framewwork. This
capability is paramount for module development sicne it greatly reduces overall
development time.

## Faux Device & Internal Switch

For continuous integration testing, a [simulated _faux device_](faux.md) is used
to provide a reasonable emulation of any feature (e.g. bad DHCP client)
that needs to be tested by the framework at some point. This is manifested
by the [_emulation_ topology](topologies.md) that is the simplest system model.

Similarly, for most simulation uses it's better to run using an internal OVS switch with
the Faux devices, removing the dependency on physical infrastruture. The system ultimately
needs to work in both, but developing against a virtual environment is typically much
faster than continually working with physical components (unless actively debugging
problems that only manifest themselves physically). If there is a problem in the 'real'
world, then the first step is typically to try and reproduce it virtually.

## Travis CI

Travis is used as the primary CI testing point for DAQ. The
[facuetsdn/daq dashboard](https://travis-ci.com/faucetsdn/daq/branches) shows the
status of the current master branch. It is generally recommended to set up
Travis on your personal repos to test any branches you push/commit. PRs will
automatically be tested under the destination repo.

Travis runs a suite of tests defined in the `.travis.yml` file. Each `DAQ_TEST`
entry triggers a separate run through the `bin/test_daq` script. E.g. `DAQ_TEST=many`
ultimately runs `testing/test_many.sh`.  The test output results are compared against
the golden `.out` file (e.g. `testing/test_many.out`) and the tests pass if there
is no difference. (Look in `bin/test_daq` to see exactly what it's doing.)

If there are unexplained differences in the `.out` file, then the test output log
itself should be checked to see what actually went wrong, since there's likely
not enough information in the `.out` files to diagnose effectively. The complete
log output is avaliable from a Travis run (or locally when you run locally), and
the triggering line from the `.out` difference should be there as well (search for it!).

## Local Integration Tests

Tests can be run locally with something like `sudo testing/test_aux.sh`, and the output
will be generated into, e.g., `out/test_aux.out`, that can be compared against the
corresponding golden `.out` file, e.g., `misc/test_aux.out`. Running tests locally is
not always 100% exactly the same as running things in a real (against physical devices
on a physical switch) or CI environment, but in most cases it provides a workable method.

It is recommended to start from a clear DAQ configuration by running `rm -rf local`
from the main DAQ folder before running the local integration tests.

When developing a new test, the output should appear in the corresponding `.out` file,
which should be updated appropriatley. The easiest way to migrate in new changes is to
just copy the `out/` file to `testing/`, but care must be taken that only expected
changes are included with a new PR. Ultimately the Travis CI tests must pass, not the
local tests, to guard against any local filesystem changes.

## Aux Golden Device Report

The `testing/test_aux.sh` integration test generates a sample device report and
compares it against the 'golden' device report in `docs/device_report.md`. This
provides the 'end user' validation that a generated report is correct. Before
comparison, the files are automatically redacted to make transitory differences
not a cause for failure. Some of the items that will be redacted include, but are
not limited to:
* Anything after a %%
* Dates & Timestamps
* DAQ Version
* IP Addresses

One easy way to generate a new golden report file is to run the aux test locally, as
described in the next section, and use the report file geneated in the `out/` directory
as the new golden file (i.e., copy it from `out/report_9a02571e8f01_???.md` to
`docs/device_report.md`.

## Lint Checks

Lint checks are performed as part of the `testing/test_aux.sh` script. They are extra
tricky because they are typically very sensitive to the exact version of every package
installed, so they're somewhat unreliable except when run through a pristine environment
on Travis.
