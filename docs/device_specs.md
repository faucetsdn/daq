# Device Configuration

Device-specific configuration for testing is managed through a
"device specification" file that is indexed by the `device_specs` configuration
parameter, usually through `local/system.conf`. See `misc/device_specs.json`
for a baseline (used for regression tests).

The basic structure is the devices sorted by MAC address. Within each device
spec, there are a couple of relevant fields:

* <b>type</b>: The type of device, used for indexing into an appropriate MUD
file. If no <em>type</em> is specified, then it defaults to <em>default</em>
and the corresponding `mud_files/default.json` MUD file. This value is
used at runtime to index a device into a MUD file based on its MAC address.
See the [MUD ACL documentation](mudacl.md) for a more detailed description
of how MUD files are applied.
* <b>group</b>: Networking group for the device, which is functionally
equivalent to a named subnet. If no <em>group</em> is specified, then it
defaults to an isolated group based on the device's MAC address. Devices in
the same group will have network reachability (sans MUD restrictions) with
a shared DHCP server (et. al.), while devices in separate groups will be
completely sequestered.

In order to test/restrict the communication between two devices, it would need
both a _group_ and _type_ entry, so they could be on the same subnet but with
restricted flows.
