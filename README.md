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

<b>TODO:</b> Rename cmd/run to something else, and make cmd/dockrun be cmd/run</b>

If this is successful the output should look something like (after the initial download):

<pre style="margin-left:1em">
$ cmd/dockrun 
Configuring apparmor...
apparmor_parser: Unable to remove "/usr/sbin/tcpdump".  Profile doesn't exist
Starting runner ...
Replacing local/system.conf with version from /root/daq/inst...
Last DAQ commit fatal: Not a git repository (or any of the parent directories): .git
Last FAUCET commit fatal: Not a git repository (or any of the parent directories): .git
 * Starting Docker: docker                                                                                                                                                                                               [ OK ] 
ovsdb-server is not running
ovs-vswitchd is not running
 * /etc/openvswitch/conf.db does not exist
 * Creating empty database /etc/openvswitch/conf.db
 * Starting ovsdb-server
 * system ID not configured, please use --system-id
 * Configuring Open vSwitch system IDs
 * Starting ovs-vswitchd
 * Enabling remote OVSDB managers
Setting daq_intf not defined, defaulting to auto-start faux device.
Implicitly running faux device...
Launching faux ...
Removing old interface faux
Adding new interface...
Done with faux device launch.
3: faux@if2: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state LOWERLAYERDOWN group default qlen 1000
    link/ether aa:93:b6:aa:1b:ab brd ff:ff:ff:ff:ff:ff link-netnsid 1
*** Error setting resource limits. Mininet's performance may be affected.
INFO:root:Starting faucet...
INFO:root:Starting mininet...
*** Configuring hosts
networking dummy 
*** Starting controller
controller 
*** Starting 1 switches
pri ...
INFO:root:Waiting for system to settle...
INFO:root:Attaching device interface faux...
INFO:root:Adding fake external device 192.168.84.5
INFO:root:Ping test networking->dummy
INFO:root:Ping test dummy->networking
INFO:root:
INFO:root:Starting new test run 5acbe372
INFO:root:Flapping faux device interface.
INFO:root:Waiting for port-up event on interface faux port 3...
INFO:root:Recieved port up event on port 3.
INFO:root:Waiting for dhcp reply from networking...
INFO:root:Received reply, host faux is at a2:6e:bb:3a:cd:aa/10.0.0.227
INFO:root:Running background monitor scan for 10 seconds...
INFO:root:Running test suite against target...
INFO:root:Ping test networking->10.0.0.227
INFO:root:PASSED test mudgee
INFO:root:PASSED test pass
INFO:root:FAILED test fail with error 1
INFO:root:PASSED test ping
INFO:root:FAILED test bacnet with error 1
INFO:root:PASSED test nmap
INFO:root:Done with tests
INFO:root:
</pre>

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
