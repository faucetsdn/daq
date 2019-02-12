# Device Qualification Overview

One primary function of DAQ is the ability to automatically (and continuously) test devices against
a set of recognized standards. The goal is to increase the overall security level of devices to
help prevent system compromise.

## Quickstart

Running `bin/setup_daq` will setup all key components and the basic prerequisites.
For the system overall, this installs a minimum set of basic packages, docker, and openvswitch.
Additionally, it sets up a local install of required packages and components.

Once installed, the basic qualification suite can be run with `cmd/run -s`. The `-s`
means <em>single shot</em> and will run tests just once and then exit (see the
[options documentation](options.md) for more details). The `local/` directory is 
created upon first execution of `cmd/run`. Runtime configuration
is always pulled from `local/system.conf`, and if this file does not exist a baseline
one will be copied from `misc/system_base.conf`.
The output should approximately look like this [example log output](run_log.md).

## Configuration

After an initial test-install run, edit `local/system.conf` to specify the network adapter
name(s) of the device adapter(s) or external physical switch.
If the file does not exist, it will be populated with a default version on system start with
defaults that use the internal _faux_ test client: This is recommended the first time around
as it will test the install to make sure everything works properly. The various options are
documented in the configuration file itself. Note that the file follows "assignment" semantics,
so the last declaration of a variable will be the only one that sticks. (The `local/`
subdirectory contains all information local to the DAQ install, such as configuration information
or cloud credentials.)

## Report Generation

After a test run, the system creates a <em>test report document</em> in a file that is named
something like <code>inst/report_<em>ma:ca:dd:re:ss</em>_<em>timestamp</em>.txt</code>. This file
contains a complete summary of all the test results most germane to qualifying a device (but is not
in iteself comprehensive). If properly configured, this report will be uploaded to the configured
cloud instance and available for download from the Web UI.

## Qualification Dashboard

The (optional) cloud dashboard requires a service-account certification to grant authorization.
Contact the project owner to obtain a new certificate for a dashboard page on an already
existing cloud project. Alternatively set up a new project by following the
[Firebase install instructions](firebase.md). The `bin/stress_test` script is useful for
setting up a continuous qualification environment: it runs in the background and pipes the output
into a rotating set of logfiles.

## Containerized Tests

The majority of device tests are run as Docker containers, which provides a convenient bundling of
all the necessary code. The `docker/` subdirectory contains a set of Docker files that are used
by the base system. Local or custom tests can be added by following the
["add a test" documentation](add_test.md). Tests are generally supplied the IP address of the
target device, which can then be used for any necessary probes (e.g. a nmap port scan).

## Debugging

The `inst/` subdirectory is the <em>inst</em>ance runtime directory, and holds all the resulting
log files and diagnostic information from each run. There's a collection of different files in
there that provide useful information, depending on the specific problem(s) encountered. A device's
[startup sequence log](startup_pcap.md) provides useful debugging material for intial device
phases (e.g. DHCP exchange).

Command-line options that can be supplied to most DAQ scripts for diagnostics:
* `-s`: Only run tests once, otherwise loop forever.
* `-e`: Activate tests on device plug-in only, otherwise test any active port.
* `daq_loglevel=debug`: Add debug info form the DAQ test runner suite.
* `mininet_loglevel=debug`: Add debug info from the mininet subsystem (verbose!)

See the [options documentation](options.md) file for a more complete
description of all the configuration options.

## Network Taps

The startup (including DHCP negotiation and baseline ping tests) network capture can be found
in the node-specific directory, and can be parsed using tcpdump with something like:

`tcpdump -en -r inst/run-port-01/nodes/gw01/tmp/startup.pcap ip`

The [example pcap output file](startup_pcap.md) shows what this should look like for a
normal run (replace `01` with the appropriate port set number).
