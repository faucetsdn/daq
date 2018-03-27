# DAQ: <b>D</b>evice <b>A</b>utomated <b>Q</b>ualification for IoT Devices.

Flexble IoT device qualification framework utilizing the FAUCET SDN controller.

## Build instructions

### Prerequisites

Tested with ```Linux 4.9.0-5-amd64 #1 SMP Debian 4.9.65-3+deb9u2 (2018-01-04) x86_64 GNU/Linux```, YMMV.

* Install [Open vSwitch Debian Install](http://docs.openvswitch.org/en/latest/intro/install/distributions/#debian)
  (tested with version 2.6.2).
* Install [Docker CE Debian Install](https://docs.docker.com/install/linux/docker-ce/debian/)
  (tested with version 17.12.0-ce).
* Also need to add user to docker group (as described on install docker page).

### Building DAQ

The build setup first builds containers for basic execution, then a docker container for docker-in-docker execution.

<pre>
  $ cmd/build
  # Get tea since this could take upwards of 15 minutes for a clean build.
</pre>

You can also clean all the stuffs using <code>cmd/clean</code>, which is sometimes necessary to gaurintee a clean build.
Be warned, it also might clean some other images/containers from other projects.

### Configuring DAQ

<code>system.conf</code>

### Running DAQ

You can run the containerized version using <code>cmd/dockrun</code> to avoid any additional setup.

For active development, you'll need to install things as indicated in <code>docker/Dockerfile.runner</code>
and then run using <code>cmd/run</code>.
