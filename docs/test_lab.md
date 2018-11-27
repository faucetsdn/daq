# Test Lab Setup

The basic _Test Lab Setup_ is designed to test ~10 devices at a time using a physical network
switch. Additionally, it is the minimum setup to test switch-specific functionality such as PoE.
Although hooked together through one switch, dynamic network configuration is used to control
dataflow in the system, following the outline in the [device specs](device_specs.md) docs: by
defailt, all devices are completely sequestered and tested as if they were the only one on the
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
3. _eXtra_ devices (not required) that can be used to run a simulated device on the controller
host. 3x eXtra is recommened for a full test lab setup because it allows for running
[core FAUCET switch tests](https://faucet.readthedocs.io/en/latest/testing.html#hardware-switch-testing-with-docker).
At least 1 eXtra is useful for diagnosing any switch configuration problems.

## Configuration

Configuring the test lab switch requires a few separate pieces of setup:
1. The [FAUCET Vendor-Specific Documentation](https://docs.faucet.nz/en/latest/vendors/index.html)
for the specific switch used in any setup, including the necessary OpenFlow controller
configuration (such as the port used for the control plane uplink).
2. System configuration of the controller host. See `misc/system_phy.conf` for an example
configuration for an external physical switch. Key entries are:
    * `ext_dpid`: Data plane ID for the connected physical switch.
    * `ext_ctrl`: Interface name of the control-plane network.
    * `ext_pri` : Interface name of the data-plane network.
    * `ext_ofip`: Control plane interface IP address (and subnet).
    * `ext_addr`: External switch IP address (used to verify the connection).
    * `sec_port`: Port of secondary (external) switch for the data-plane uplink (defaults to 7).

## Testing

The `bin/physical_sec` script will setup and test the basic connection to the external physical switch:
<pre>
~/daq$ <b>bin/physical_sec</b>
Loading config from local/system.conf
Configuring control interface enx00e04c68036b at 192.0.2.10/16
Checking external connection to 192.0.2.138
PING 192.0.2.138 (192.0.2.138) 56(84) bytes of data.
64 bytes from 192.0.2.138: icmp_seq=1 ttl=64 time=2.79 ms

--- 192.0.2.138 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 2.790/2.790/2.790/0.000 ms

DAQ autoclean ip link set down dev enx00e04c68036b
Done with physical switch configuration.
</pre>

## Common Errors

The following message in `inst/faucet.log` indicates that a switch is trying
to connect to faucet, but `ext_dpid` is configured wrong: simply copy/paste
the hex dipd (e.g. _0x1aeb960541_) into the config file.
<pre>
Nov 20 23:23:56 faucet ERROR    <ryu.controller.ofp_event.EventOFPSwitchFeatures object at 0x7fd22a14dcc0>: unknown datapath DPID 115621627201 (0x1aeb960541)
</pre>
