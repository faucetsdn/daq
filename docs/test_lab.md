# Test Lab Setup

The basic _Test Lab Setup_ is designed to test ~10 devices at a time using a physical network
switch. Additionally, it is the minimum setup to test switch-specific functionality such as PoE.
Although hooked together through one switch, dynamic network configuration is used to control
dataflow in the system, following the outline in the [device specs](device_specs.md) docs: by
default, all devices are completely sequestered and tested as if they were the only one on the
switch.

## Architecture

```
           Internet
              |
              |
       +--------------+
       |              |
       |  Controller  |
       |              |
       +--------------+
         |    |    |       C = Control-plane network
         |C   |D   |(X)    D = Data-plan network
         |    |    |       X = eXtra network(s)
       +--------------+
       |              |
       |    Switch    |
       |              |
       +--------------+
          |        |
          |        |
       +-----+  +-----+
       |     |  |     |
       | DUT |  | DUT |  DUT = Device Under Test
       |     |  |     |
       +-----+  +-----+

```

## Components

There are three main components:
1. _Controller_ runs DAQ and FAUCET. This should be any resonably common Debian distribution
(Ubuntu ok), and nearly be anything such as a standard laptop or desktop tower. Production
grade systems would be something akin to a Dell R230.
2. _Switch_ needs to be an OpenFlow/FAUCET compatible switch, as outlined in the
[FAUCET Hardware Switch](https://faucet.readthedocs.io/en/latest/vendors/index.html) documentation.
For a general purpose setup any of the enterprise-grade switches should suffice, although specific
switches might be more appropriate depending on the exact objectives of the lab.
3. _DUT_ is whatever device is intended for testing. For diagnostics, it is possible to loop back,
using a physical cable, a switch port to another network adapter on the controller machine.

## Connections

There are several (minimum two) network connections (ethernet cables) required between the switch
and controller machines. A standard USB-dongle Ethernet adapter should be sufficient for each.
1. _Control_ plane, which supports the OpenFlow controller connection between switch and controller
host. The port used for this is defined as part of the vendor-specific switch setup (see below).
2. _Data_ plane connection, which provides for all data access for the devices. Internet access for
the devices will be filtered/proxied through the controller host. The port used for this is defined
by the `sec_port` config (see below).
3. _eXtra_ devices, also known as _faux_ devices (not required), can be used to run a simulated
device on the controller host.

### Extra Network Connections

* To create _eXtra/faux_ devices, use `cmd/faux :[interface name]`, ie `cmd/faux :eth1`.
* At least 1 eXtra is useful for diagnosing switch configuration problems.
* 3 or more eXtra are recommended for a full test lab setup because it allows running
[core FAUCET switch tests](https://faucet.readthedocs.io/en/latest/testing.html#hardware-switch-testing-with-docker).

## Configuration

Configuring the test lab switch requires a few separate pieces of setup:
1. The [FAUCET Vendor-Specific Documentation](https://docs.faucet.nz/en/latest/vendors/index.html)
for the specific switch used in any setup, including the necessary OpenFlow controller
configuration (such as the port used for the control plane uplink).
2. System configuration of the controller host. See `config/system/ext.yaml` for an example
configuration for an external physical switch. Key entries are:
    * `ext_dpid`: Data plane ID for the connected physical switch.
    * `ext_ctrl`: Interface name of the control-plane network.
    * `ext_intf`: Interface name of the data-plane network.
    * `ext_ofpt`: Controller OpenFlow port (defaults to 6653).
    * `ext_ofip`: Controller control plane IP address (and subnet).
    * `ext_addr`: External switch IP address (used to verify the connection).
    * `sec_port`: Port of secondary (external) switch for the data-plane uplink (defaults to 7).

## Troubleshooting

### Basic network connection

The `bin/physical_sec` script will setup and test the basic connection to the external physical switch:
<pre>
~/daq$ <b>bin/physical_sec</b>
Loading config from local/system.conf
Configuring control interface enxb49cdff33ad9 at 192.168.1.10/16
enxb49cdff33ad9: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.1.10  netmask 255.255.0.0  broadcast 0.0.0.0
        ether b4:9c:df:f3:3a:d9  txqueuelen 1000  (Ethernet)
&hellip;

enx645aedf345fa: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        ether 64:5a:ed:f3:45:fa  txqueuelen 1000  (Ethernet)
&hellip;

Checking external connection to 192.168.1.2
PING 192.168.1.2 (192.168.1.2) 56(84) bytes of data.
64 bytes from 192.168.1.2: icmp_seq=1 ttl=64 time=3.38 ms

--- 192.168.1.2 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 3.382/3.382/3.382/0.000 ms

DAQ autoclean ip link set down dev enxb49cdff33ad9
Done with physical switch configuration.
</pre>

### Control Plane Interface Link

Looking at the control plane network interface can give some diagnostics about the switch setup.
Using <code>tcpdump -ni <em>{ext_ctrl}</em></code> should show the switch `ext_addr` address
(_192.168.1.2_), the expected `ext_ofip` controller address (_192.168.1.10_) and `ext_ofpt`
configured port (_6653_). (It's not easy to tell if the controller subnet is misconfigured.)

<pre>
~/daq$ <b>sudo tcpdump -ni enxb49cdff33ad9</b>
&hellip;
11:30:47.739506 IP <b>192.168.1.2</b>.37422 > <b>192.168.1.10</b>.<b>6653</b>: Flags [S], seq 2153185008, win 29200, options [mss 1460,sackOK,TS val 38338000 ecr 0,nop,wscale 7], length 0
&hellip;
</pre>

If there's a string of unfulfilled ARP requests, then it likely means the `ext_ofip` is
configured incorrectly.
<pre>
~/daq$ <b>sudo tcpdump -ni enxb49cdff33ad9</b>
&hellip;
11:34:04.739266 ARP, Request who-has <b>192.168.1.10</b> tell 192.168.1.2, length 46
11:34:08.738730 ARP, Request who-has 192.168.1.10 tell 192.168.1.2, length 46
11:34:09.738947 ARP, Request who-has 192.168.1.10 tell 192.168.1.2, length 46
&hellip;
</pre>

### Determining Data Plane ID.

The message below, in `inst/faucet.log`, indicates that a switch is trying
to connect to faucet, but `ext_dpid` is configured wrong: simply copy/paste
the hex dipd (_0x1aeb960541_) from `inst/faucet.log` into `local/system.conf`.
<pre>
~/daq$ <b>tail -f inst/faucet.log</b>
&hellip;
Nov 20 23:23:56 faucet ERROR    <ryu.controller.ofp_event.EventOFPSwitchFeatures object at 0x7fd22a14dcc0>: unknown datapath DPID 115621627201 (<b>0x1aeb960541</b>)
</pre>

Be careful that the error doesn't come from a locally configured OVS instance. Check
the output of `ovs-vsctl show` to make sure the wrong virtual bridge isn't running
and confusing the logs. When DAQ is running configured for a physical switch,
there should only be _one_ Bridge named `pri` shown: if there's another (typically
named `sec`) bridge shown, then it means the system still thinks it's running with a
non-physical switch (missing the `ext_intf` setting).
<pre>
~/daq$ <b>sudo ovs-vsctl show | fgrep Bridge</b>
    Bridge pri
~/daq$
</pre>
