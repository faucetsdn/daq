## DAQ Command Line Options

Simple command line arguments. Can also be specified as a long-form argument (i.e. `-s` <=> `single_shot=true`):

* `-s`, `single_shot`: Don't repeat tests, only do one run.
* `-e`, `event_trigger`: Wait for port up trigger to start.
* `-c`, `use_console`: Escape to console rather than exit.
* `-l`, `result_linger`: Keep services in place on failure.
* `-d`, `debug_mode`: Shorthand for enabling debug mode options.

Long-form arguments:

* `daq_loglevel`: Set log-level for daq-based logging commands.
* `mininet_loglevel`: Set log-level for underlying mininet commands.

e.g.: `cmd/exrun -s daq_loglevel=debug`
