# Test Lab Setup

The basic _Test Lab Setup_ is designed to test ~10 devices at a time using a physical network switch. Additionally,
it is the minimum setup to test switch-specific functionality such as PoE.

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
1. _Controller_ runs DAQ and FAUCET. This should be any resonably common Debian distribution (Ubuntu ok), and
nearly be anything such as a standard laptop or desktop tower. Production grade systems will be something akin to a Dell R230.
2. _Switch_ needs to be an OpenFlow/FAUCET compatible switch, as outlined in the
[FAUCET Hardware Switch](https://faucet.readthedocs.io/en/latest/vendors/index.html) documentation. For a general
purpose setup any of the enterprise-grade switches should suffice, although specific switches might be more
appropriate depending on the exact objectives of the lab.
3. _DUT_ is whatever device is intended for testing. There is no canonical test-lab device, although there is an
[Android Things](https://developer.android.com/things/) image available that can be used to test some capabilities.

## Connections

There are several (minimum two) network connections (ethernet cables) required between the switch and
controller machines. A standard USB-dongle Ethernet adapter should be sufficient for each.
1. _Control_ plane which supports the OpenFlow controller connection between switch and controller host.
2. _Data_ plane connection which provides for all data access for the devices. Internet access for the devices will
be filtered/proxied through the controller host.
3. _eXtra_ devices (not required) that can be used to run a simulated device on the controller host. 3x eXtra
is recommened for a full test lab setup because it allows for running
[core FAUCET switch tests](https://faucet.readthedocs.io/en/latest/testing.html#hardware-switch-testing-with-docker).
At least 1 eXtra is useful for diagnosing any switch configuration problems.

## Configuration

Configuring the test lab switch requires a few separate pieces of setup:
1. The [FAUCET Vendor-Specific Documentation](https://docs.faucet.nz/en/latest/vendors/index.html) for
the specific switch used in any setup, including the necessary OpenFlow controller configuration.
2. Network topology configuration of the controller host. See `misc/faucet_phy.yaml` for an example
configuration for an external physical switch. Key points:
    * Interface `name` for the data-plane network `pri` switch staking port.
    * 'dp_id` value for the `sec` switch.
    * `description: DAQ autostart` clause for `sec` switch to auto-configure the external interface.
3. System configuration for controller communication, in the `local/system.conf` file.
See `misc/system.conf.example_phy` for an example of what this looks like.
    * `ext_ctrl`: interface name of the control-plane network.
    * `ext_ofip`: ip address (and subnet) to use on the control interface.
    * `ext_addr`: ip address of the switch (used to verify the connection).
    * 'network_config': points to the appropriate faucet config file.
