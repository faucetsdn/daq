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

### Configuration

After an initial test-install run, edit <code>local/system.conf</code> appropriately.
If the file does not exist, it will be populated with a default version on system start.
This is recommened the first time around as it will use the internal 'faux' test device
to make sure everything works.

### Running DAQ

Normal execution can be invoked using the containerized build. The first thing this will do,
if necessary, is download the container image (which can take a bit of time).

<pre>
  $ cmd/dockrun
</pre>

If this is successful the output should look something like (after the initial download):

<pre>
  $ cmd/dockrun
  ...
  ...
  ...
  ...
</pre>

<b>TODO:</b> Rename cmd/run to something else, and make cmd/dockrun be cmd/run</b>

### Building DAQ

You shouldn't need to do this unless you're doing active development on DAQ itself. Doing this
will require installing more prerequisites that aren't indicated above. See
<code>bin/setup_install</code> or <code>docker/Docker.base</code> for details.

To build containers for basic execution, which can take a long time:

<pre>
  $ cmd/build
</pre>

To run the development version, use the simple run command:

<pre>
  $ cmd/run
</pre>

Build the runner container, which can take a really long time:

<pre>
  $ cmd/inbuild
</pre>

You can also clean all the stuffs:

<pre>
  $ cmd/clean
</pre>

...which is sometimes necessary to gaurintee a clean build.
Be warned, it also might clean some other images/containers from other projects.
