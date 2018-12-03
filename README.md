# DAQ: <b>D</b>evice <b>A</b>utomated <b>Q</b>ualification for IoT Devices.

A flexible IoT Device Automated Qualification (DAQ) framework utilizing the FAUCET SDN controller.
More details about goals and objectives can be found in the IEEE Computer article
[Taming the IoT: Operationalized Testing to Secure Connected Devices](https://www.computer.org/csdl/mags/co/2018/06/mco2018060090-abs.html).
Join the [daq-users@googlegroups.com](https://groups.google.com/forum/#!forum/daq-users) email
list for ongoing discussion about using DAQ for device testing.

The goal is to provide an IoT testing framework with three main objectives:
* Test enterprise IoT devices for compliance to established network & security standards.
* Use TDD methodologies to push IoT specifications out to device developers.
* Dynamically manage network infrastructure to appropriately restrict communication patterns.

## System Requirements

* Linux install: DAQ has been tested against both `Ubuntu 16.04.4 LTS xenial` and
`Debian GNU/Linux 9.4 stretch`, YMMV with other platforms.
* Dedicated network adapters: At the very minimum one dedicated ethernet adapter is
required. This could either be a separate built-in NIC, or a USB-Ethernet dongle.
* (Optional) OpenFlow-compatible hardware switch: See instructions below on setup.

## Quickstart

Running `bin/setup_base` will setup the basic prerequisites. This will install a
minimum set of basic packages, docker, and openvswitch.

Once installed, the basic qualification suite can be run with `cmd/run -s`. The `-s`
means <em>single shot</em> and will run tests just once and then exit (see the
[options documentation](docs/options.md) for more details). Runtime configuraiton
is always pulled from `local/system.conf`, and if this file does not exist a baseline
one will be copied from `misc/system_base.conf`.
The output should approximately look like this [example log output](docs/run_log.md).

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
something like <code>inst/report_<em>ma:ca:dd:re:ss</em>.txt</code>. This file contains a complete summary
of all the test results most germane to qualifying a device (but is not in iteself comprehensive).

## Network Topologies

There are several level of network topologies that are used for different testing purposes
(detailed in the [Network Topologies](docs/topologies.md) subsection), covering the range from
single-device testing through to a production-class environment.
The recommended course is to start with the simplest (software emulation) and progress
forward as required for a specific project.

## Qualification Dashboard

The (optional) cloud dashboard requires a service-account certification to grant authorization.
Contact the project owner to obtain a new certificate for a dashboard page on an already
existing cloud project. Alternatively set up a new project by following the
[Firebase install instructions](docs/firebase.md). The `bin/stress_test` script is useful for
setting up a continuous qualification environment: it runs in the background and pipes the output
into a rotating set of logfiles.

## Containerized Tests

The majority of device tests are run as Docker containers, which provides a convenient bundling of
all the necessary code. The `docker/` subdirectory contains a set of Docker files that are used
by the base system. Local or custom tests can be added by following the
["add a test" documentation](docs/add_test.md). Tests are generally supplied the IP address of the
target device, which can then be used for any necessary probes (e.g. a nmap port scan).

## Debugging

The `inst/` subdirectory is the <em>inst</em>ance runtime directory, and holds all the resulting
log files and diagnostic information from each run. There's a collection of different files in
there that provide useful information, depending on the specific problem(s) encountered. A device's
[startup sequence log](docs/startup_pcap.md) provides useful debugging material for intial device
phases (e.g. DHCP exchange).

Command-line options that can be supplied to most DAQ scripts for diagnostics:
* `-s`: Only run tests once, otherwise loop forever.
* `-e`: Activate tests on device plug-in only, otherwise test any active port.
* `daq_loglevel=debug`: Add debug info form the DAQ test runner suite.
* `mininet_loglevel=debug`: Add debug info from the mininet subsystem (verbose!)

See the [options documentation](docs/options.md) file for a more complete
description of all the configuration options.

## Network Taps

The startup (including DHCP negotiation and baseline ping tests) network capture can be found
in the node-specific directory, and can be parsed using tcpdump with something like:

`tcpdump -en -r inst/run-port-01/nodes/gw01/tmp/startup.pcap ip`

The [example pcap output file](docs/startup_pcap.md) shows what this should look like for a normal run.
(Replace `01` with the appropriate port set number.)

If there are device-level network problems then it is possible to use `tcpdump` or similar
to examine the network traffic. When using the `cmd/run` command, the system runs the
framework in a Docker container named `daq-runner` and it moves the test
network interface(s) into that container. Any tap command must be also run in the container, so it
looks something like (replacing `faux` with the real adapter name):

`docker exec daq-runner tcpdump -eni faux`

(If you are monitoring a full hardware setup with a physical switch, and not an individual
device adapter, the packets will be tagged by VLAN that corresponds to the device port on the
switch itself.)

## Build Setup

'Building' DAQ is only required for active framework development. Otherwise, stick
with the packaged runner.  There are a bunch of additional dependenicies and extra
development steps required. See the [build documentation](docs/build.md) for more details
on how to build the development system.
