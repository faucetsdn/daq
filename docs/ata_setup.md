# Assembly Test Appliance (ATA) Setup Documentation

The [ata.yaml](../config/system/ata.yaml) daq configuration file
shows a baseline example of how to setup a DAQ install for network diagnostics.

Key fields of interest:
* `switch_setup:`
  * `data_intf:` Network interface used to talk to the target test network. This could
  either be a built-in ethernet adapter or USB dongle.
  * `data_mac:` MAC address (optional) to use for the network interface. This is
  necessary if, for example, there is a specific MAC address required for network auth.
  * `model: EXT_STACK` Indicator that this is running with an external network stack.
* `run_trigger:`
  * `native_vlan: 122` The vlan to use internally. Actual value shouldn't matter
  as long as it's non-zero.
* `internal_subnet:`
  * `subnet: 10.21.0.0./16` This specifies the subnet to use internally to the
  system. If it conflicts with the external target network subnet, then there
  will be problems (requiring dev work to fix).


A minimum system can be setup by creating a `local/system.yaml` file that contains
something like:
```
include: ${DAQ_LIB}/config/system/ata.yaml

switch_setup:
    data_intf: enx00e04c680029
```
(i.e., only the `data_intf` field is likely necessitated to be unique to a given system
intall, everything else can likely just be the defaults)

To run the system, a simple `cmd/run` should suffice, or `cmd/run -s` if you just want
to scan the network for at least one device.

The system relies on ARP broadcast to discover hosts... so it might take a while (arp
cache timeout), or try to disconnect/reconnect a device.

After the run, the results are uncerimoniously dumped in the various run directories,
i.e. `inst/run-MACADDRESS/`, try `ls -d inst/run-*` for a list of all devices scanned.
