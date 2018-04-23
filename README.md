# DAQ: <b>D</b>evice <b>A</b>utomated <b>Q</b>ualification for IoT Devices.

Flexble IoT device qualification framework utilizing the FAUCET SDN controller.

## Build instructions

### Prerequisites

Tested with ```Linux 4.9.0-5-amd64 #1 SMP Debian 4.9.65-3+deb9u2 (2018-01-04) x86_64 GNU/Linux```, YMMV.

You should be able to run <b><code>bin/setup_install</code></b> to setup the basic prerequisites. This
should install some basic packages, docker, and openvswitch.

### Configuration

After an initial test-install run, edit <code>local/system.conf</code> appropriately.
If the file does not exist, it will be populated with a default version on system start.
This is recommened the first time around as it will use the internal 'faux' test device
to make sure everything works.

### Running DAQ

Normal execution can be invoked using the containerized build. The first thing this will do,
if necessary, is download the container image (which can take a bit of time). The '-s' means
to run once and exit, the '-a' means to automatically detect and connect to devices.

<pre>
  $ <b>cmd/run -s -a</b>
</pre>

See below for a sample output of a successful run.

### Options and Debugging

Configuration options can either be specified in the local/system.conf file, or on the command line.
For debugging fun, try:

<pre>
  $ <b>cmd/run -s -a daq_loglevel=debug mininet_loglevel=debug</b>
</pre>

See misc/system.conf for a more detailed overview of options.

### Building DAQ

You shouldn't need to do this unless you're doing active development on DAQ itself. Doing this
will require installing more prerequisites that aren't indicated above. See
<code>bin/setup_install</code> or <code>docker/Docker.base</code> for details.

To build containers for basic execution, which can take a long time:

<pre>
  $ <b>cmd/build</b>
</pre>

To run the development version, use the simple executor-run command:

<pre>
  $ <b>cmd/exrun</b>
</pre>

Build the runner container, which can take a <em>really</em> long time:

<pre>
  $ <b>cmd/inbuild</b>
</pre>

You can also clean all the stuffs:

<pre>
  $ <b>cmd/clean</b>
</pre>

...which is sometimes necessary to gaurintee a clean build.
Be warned, it also might clean some other images/containers from other projects.

### External Ethernet Adapter.

To use an external physical ethernet adapter with a real device, rather than the internal faux device,
simply edit the <code>local/system.conf</code> file to specify the eth interface to use. See the
documentation in the config file itself for details on the available settings.

### External and Physical switches.

See the <a href="https://github.com/faucetsdn/faucet/tree/master/docs/vendors">Faucet vendor-specific docs</a>
for how to setup hardware for testing. Some convenience scripts:

* <code>bin/external_ovs</code> sets up an external (to daq) ovs instance for testing stacked configurations.
* <code>bin/physical_sec</code> sets up a physical secondary switch for proper hardware testing.

### Example Output

<pre style="margin-left:1em">
$ <b>cmd/run -s -a</b>
Configuring apparmor...
apparmor_parser: Unable to remove "/usr/sbin/tcpdump".  Profile doesn't exist
Starting runner -s -a...
Replacing local/system.conf with version from /root/daq/inst...
Copying default system.conf to local/system.conf
Loading daq run configuration from local/system.conf
 * Starting Docker: docker                                                                                                                                  [ OK ] 
ovsdb-server is not running
ovs-vswitchd is not running
 * /etc/openvswitch/conf.db does not exist
 * Creating empty database /etc/openvswitch/conf.db
 * Starting ovsdb-server
 * system ID not configured, please use --system-id
 * Configuring Open vSwitch system IDs
 * Starting ovs-vswitchd
 * Enabling remote OVSDB managers
Implicitly running faux device...
Launching faux ...
Removing old interface faux
Adding new interface...
Done with faux device launch.
3: faux@if2: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state LOWERLAYERDOWN group default qlen 1000
    link/ether 72:e2:ac:31:00:a4 brd ff:ff:ff:ff:ff:ff link-netnsid 1
Executing runner -s -a...
*** Error setting resource limits. Mininet's performance may be affected.
INFO:root:Creating ovs secondary with dpid/port 2/47
INFO:root:Added switch link pri-eth1 <-> sec-eth47
Unable to contact the remote controller at 127.0.0.1:6633
INFO:root:Starting mininet...
*** Configuring hosts

*** Starting controller
controller 
*** Starting 2 switches
pri sec ...
INFO:root:Starting faucet...
INFO:root:Waiting for system to settle...
INFO:root:Attaching device interface faux on port 1.
INFO:root:Entering main event loop.
INFO:root:Set 1 waiting to settle...
INFO:root:Set 1 activating.
INFO:root:Set 1 ping test gw01->dummy01
INFO:root:Set 1 ping test dummy01->gw01
INFO:root:Set 1 ping test dummy01->192.168.84.76
INFO:root:Set 1 ping test gw01->dummy01 from 192.168.84.76
INFO:root:Set 1 waiting for dhcp reply from gw01...
INFO:root:Set 1 received dhcp reply: 02:e3:40:cb:f3:50 is at 10.0.0.242
INFO:root:Set 1 background scan for 10 seconds...
INFO:root:Set 1 monitor scan complete
INFO:root:Set 1 ping test gw01->10.0.0.242
INFO:root:Set 1 ping test gw01->10.0.0.242 from 192.168.84.76
INFO:root:Set 1 running test pass
INFO:root:Set 1 PASSED test pass
INFO:root:Set 1 running test fail
INFO:root:Set 1 PASSED test fail
INFO:root:Set 1 running test ping
INFO:root:Set 1 PASSED test ping
INFO:root:Set 1 running test bacnet
INFO:root:Set 1 PASSED test bacnet
INFO:root:Set 1 running test nmap
INFO:root:Set 1 PASSED test nmap
INFO:root:Set 1 running test mudgee
INFO:root:Set 1 PASSED test mudgee
INFO:root:Set 1 cleanup
INFO:root:Set 1 complete, failures: []
INFO:root:Remaining sets: []
*** Stopping 1 controllers
controller 
*** Stopping 1 links
.
*** Stopping 2 switches
pri sec 
*** Stopping 0 hosts

*** Done
INFO:root:Done with runner.
Killing daq-faux container...
Done with run.
</pre>