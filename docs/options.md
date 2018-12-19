# DAQ Configuration Options

## Command Line Arguments.

Basic arguments can either be specified with the short form (`-s`)
on the command line, or with the more verbose long-form (`single_shot=true`).

* `-c`, `use_console`: Escape to console rather than exit.
* `-d`, `debug_mode`: Shorthand for enabling debug mode options.
* `-e`, `event_trigger`: Wait for port up trigger to start.
* `-f`, `fail_mode`: Fail test run immediately when any test fails.
* `-h`, `show_help`: Show help information.
* `-k`, `keep_hold`: Add a hold test that keeps runing for debugging.
* `-l`, `result_linger`: Keep services in place on failure.
* `-n`, `no_test`: Do not test devices, just put them on the network.
* `-s`, `single_shot`: Don't repeat tests, only do one run.

## `local/system.conf` File.

Additional long-form options are documented in the `misc/system.conf` file,
and can also be included on the command-line. Some useful ones for debugging
are:

* `daq_loglevel`: Set log-level for daq-based logging commands.
* `mininet_loglevel`: Set log-level for underlying mininet commands.
* `run_limit`: Set number of test runs to do before exit.

e.g.: `cmd/run daq_loglevel=debug run_limit=10`

## Common Run Invocation Examples

`cmd/run`: Run tests in a continuous loop, for any device that is plugged
into a switch port or adapter. This is the default <em>background</em> run
state for continuous testing.

`cmd/run -s`: Run tests <em>once</em> for each device, and then terminate when
there are no more active tests. This represents an <em>imperative</em> mode
when the goal is to "test this device right now."

`cmd/run -n`: Activate a device so that it is on the network, but do not
run the tests. Useful for setup and functional validation of devices.

`cmd/run -l`: Keep the system configured in an <em>active</em> state after
a test run. This is useful for debugging a system setup after testing (e.g.
to see why a test failed).

`cmd/run -e`: Only run tests when there is a specific port-up event (e.g.
plugging in a device to a network switch). This is useful to control the flow
of testing in a test-lab environment to reduce activity.

`cmd/run -f`: Fail a test run immediately when any individual test failes.
Useful for debugging the state of a single test when it fails, separating it
out from something run with a complete test suite.
