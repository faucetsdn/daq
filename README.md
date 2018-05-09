# DAQ: <b>D</b>evice <b>A</b>utomated <b>Q</b>ualification for IoT Devices.

A flexble IoT Device Automatd Qualification (DAQ) framework utilizing the FAUCET SDN controller.

## Quickstart

Running `bin/setup_install` will setup the basic prerequisites. This
will install a minimum set of basic packages, docker, and openvswitch. This has been tested on
both `Ubuntu 16.04.4 LTS xenial` and `Debian GNU/Linux 9.4 stretch`, YMMV with other platforms.

Once installed, the basic qualification suite can be run with `cmd/run -s`. (The
'-s' command line option means 'single' mode, rather than continuous test.) The first
time this is run it will download the DAQ Docker image, which can take a little while. It should
approximately look like this [example log output](docs/run_log.md).

## Configuration

After an initial test-install run, edit `local/system.conf` appropriately.
If the file does not exist, it will be populated with a default version on system start.
This is recommened the first time around as it will use the internal _faux_ test device
to make sure everything works. The various options are documented in the configuration file
itself. Note that the file folows "assignment" semantics, so the last declaration of a variable
will be the only one that sticks.

## Network Configurations

There are three variants of network configuraiton available to test devices. The recommended
course is to start with the simplest (software emulation), and progress forward as required by
the specific project. Details on required configuration options are in the config file.

1. _Software Emulation_: This uses a built-in 'faux' device to test the DAQ suite itself. It is
important to make sure this works properly to verify the basic install is sound. This
is most useful for basic system sanity checks and system development.

2. _Network Adapter_: This uses one or more physical USB interfaces to allow external
ethernet connections. There is no particular limit on the number of devices that can be connected
this way except for the limitations of the host's USB subsystem.

3. _Network Switch_: Use an external OpenFlow network switch. To do this, there'll need to be
a supported network swtich setup as described in the FAUCET documentation. See the [switch
setup documentation](docs/switches.md) for more details.

## Testing Dashboard

The (optional) cloud dashboard requires a service-account certification to grant authorization.
First, obtaining a new certificate for a page on an already existing cloud project: contact the
project owner to do this.  Alternatively set up a new project by following the
[Firebase install instructions](docs/firebase.md). The `bin/stress_test` script is useful for
setting up a continous testing environment. Mainly, it pipes the output into a rotating set of logfiles.

## Debugging

There are a numbe of command-line options that can be supplied to most DAQ scripts for diagnostics:
* `-s`: Only run tests once, otherwise loop forever.
* `-e`: Activate tests on device plug-in only, otherwise test any active port.
* `daq_loglevel=debug`: Add debug info form the DAQ test runner suite.
* `mininet_loglevel=debug`: Add debug info from the mininet subsystem (verbose!)

Note that the long-form command-line options (e.g. `daq_loglevel`) can be placed in the
`system.conf` file as well.

## Network Taps

If there are device-level network problems then it is possible to use `tcpdump` or similar
to example the network traffic. When using the `cmd/run` command, the system runts the
testing framework in a Docker container named `daq-runner`, and it moves the test
network interface(s) into that container. Any tap command must be also run in the container, so it
looks something like (substituting, of course, the actual network interface name):

`docker exec daq-runner tcpdump -eni enx9cebe840a74c`

## Build Setup

Building is only required for active test development. Otherwise, stick
with the packaged runner.  There are a bunch of additional dependicies and extra development steps.
See the [build documentation](docs/build.md) for more details on how to build the development system.
