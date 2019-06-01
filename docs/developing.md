# DAQ Developers Guide

## Travis CI

Travis is used as the primary CI testing point for DAQ. The
(facuetsdn/daq dashboard)[https://travis-ci.com/faucetsdn/daq/branches] shows the
status of the current master branch. It is generally recommended to set up
Travis on your personal repos to test any branches you push/commit. PRs will
automatically be tested under the destination repo.

Travis runs a suite of tests defined in the `.travis.yml` file. Each `DAQ_TEST`
entry triggers a separate run through the `bin/test_daq` script. E.g. `DAQ_TEST=many`
ultimately runs `testing/test_many.sh`.  The test output results are compared against
the golden `.out` file (e.g. `testing/test_many.out`) and the tests pass if there
is no difference.

If there are unexplained differences in the `.out` file, then the test output log
itself should be checked to see what actually went wrong, since there's likely
not enough information in the `.out` files to diagnose effectively. The `.out` output
should be available in the logs, so you can typically search for it to find the relevant
error position.

## Local Integration Tests

Tests can be run locally with something like `sudo testing/test_aux.sh`, and the output
will be generated into, e.g., `out/test_aux.sh`, that can be compared against the
corresponding golden `.out` file.

When developing a new test, the output should appear the the corresponding `.out` file,
which should be updated appropriatley. The easiest way to migrate in new changes is to
just copy the `out/` file to `testing/`, but care must be taken that only expected
changes are included with a new PR. Ultimately the Travis CI tests must pass, not the
local tests, to guard against any local filesystem changes.

## Lint Checks

Lint checks are performed as part of the `testing/test_aux.sh` script. They are extra
tricky because they are typically very sensitive to the exact version of every package
installed, so they're somewhat unrelaible except when run through a pristine environment
on Travis. An error output of `cmd/inbuild exit code 1` in the logs indicates that
something went wrong with the lint checks, but it can sometimes happen locally when
there is no problem on Travis (and Travis wins).
