## DAQ Command Line Options

Simple command line arguments. Can also be specified as a long-form argument (i.e. `-s` <=> `single_shot=true`):

* `-c`, `use_console`: Escape to console rather than exit.
* `-d`, `debug_mode`: Shorthand for enabling debug mode options.
* `-e`, `event_trigger`: Wait for port up trigger to start.
* `-f`, `fail_mode`: Fail execution if any test run fails.
* `-l`, `result_linger`: Keep services in place on failure.
* `-n`, `no_test`: Do not test devices, just put them on the network.
* `-s`, `single_shot`: Don't repeat tests, only do one run.

Useful long-form arguments (see `system.conf` file for a list of others):

* `daq_loglevel`: Set log-level for daq-based logging commands.
* `mininet_loglevel`: Set log-level for underlying mininet commands.
* `run_limit`: Set number of test runs to do before exit.

e.g.: `cmd/exrun daq_loglevel=debug run_limit=10`
