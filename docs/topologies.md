# Network Topologies

## General Setup

The operational network configuration is supplied by a [FAUCET config file](faucet.md)
(as indicated by the `network_config` configuration option in `system.conf`).
The general mechanism for setting up a particular topology is:
1. Copy `misc/system.conf` and `misc/faucet.yaml` to the `local/` subdirectory (creating if needed).
2. Edit `local/system.conf` as needed, namely changing `network_config` to point to `local/faucet.yaml`.
3. Edit `local/faucet.yaml` appropriately to specify the desired network topology. See the comments
at the top of various examples in `misc/faucet*.yaml` files.

## Topology Categories

The different top-level network topologies are:
1. _Emulation_: This uses a built-in 'faux' device to test the DAQ suite itself. It is
important to make sure this works properly to verify the basic install is sound. This
is most useful for basic system sanity checks and system development. See the `misc/faucet.yaml`
or `misc/faucet_multi.yaml` files for examples of how this is configured.

2. _Adapter_: This uses one or more physical USB interfaces to allow external
ethernet connections. There is no particular limit on the number of devices that can be connected
this way except for the limitations of the host's USB subsystem. See the notes at the top of
the `misc/faucet.yaml` file for instructions on how to configure this setup.

3. _Test Lab_: Use one external OpenFlow network switch detailed in the
[test lab setup](docs/test_lab.md) documentation. This is primarily designed for testing small
sets of devices (~10) or specific hardware features (such as PoE).

4. _Tiered_: Use a complete setup of multiple exteral network switches, sufficient for testing 100s
of devices. This setup will require extensive network configuration and phsical cabling to work.
(Documentation pending.)

5. _Production_: A full 'production' setup is a multi-tiered setup with full redundancy. Intended for
production-class setups that support 1000's of devices.
(Documentation pending.)
