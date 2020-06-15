# Network Topologies

## General Setup

The network topology is auto-generated based on settings in the specified `local/system.conf`
on startup. Various templates are availabile in `config/system/`:
* `config/system/base.yaml`: Single faux-device internal test setup.
* `config/system/multi.conf`: Test setup with 3 faux-devices.
* `config/system/ext.yaml`: Setup for using an external switch (physical or simulated).

The system will generate the `inst/faucet.yaml` file, which then triggers the configuration
of the underlying OpenFlow system. General network debugging information can be found in
`inst/faucet.log`, which will generally indicate any networking activity (device port detection)
and/or misconfigured switch topologies.

## Topology Categories

The different top-level network topologies are:
1. _Emulation_: This uses a built-in 'faux' device to test the DAQ suite itself. It is
important to make sure this works properly to verify the basic install is sound. This
is most useful for basic system sanity checks and system development. See `config/system/base.yaml`
or `config/system/multi.conf` for examples of how this is configured.

2. _Adapter_: This uses one or more physical USB interfaces to directly connect
devices (no external switch). There is no particular limit on the number of devices that can be
connected this way except for the limitations of the host's USB subsystem. See the notes at the
top of the `config/system/base.conf` file for instructions on how to configure this setup.

3. _Test Lab_: Use one external OpenFlow network switch detailed in the
[test lab setup](test_lab.md) documentation. This is primarily designed for testing small
sets of devices (~10) or specific hardware features (such as PoE).

4. _Tiered_: Use a complete setup of multiple exteral network switches, sufficient for testing 100s
of devices. This setup will require extensive network configuration and phsical cabling to work.
(Documentation pending.)

5. _Production_: A full 'production' setup is a multi-tiered setup with full redundancy. Intended for
production-class setups that support 1000's of devices.
(Documentation pending.)
