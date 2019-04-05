# Device Configuration

There are three levels of device configuration:
1. [Device Descriptions](#device-descriptions): Flavor text for report generation.
2. [Device Groupings](#device-groupings): Testing groups for synchronization and subnets.
3. [Device Topologies](#device-topologies): Fine-grain network reachability control.

## Device Descriptions

Device descriptions are simple text files indexed by MAC address included in generated
reports. Located by default in
<code>local/site/mac_addrs/<em>macaddressXX</em>/report_description.txt</code>,
they are copied unmodified into the report. See
[`misc/test_site/mac_addrs/9a02571e8f00/report_description.txt`](../misc/test_site/mac_addrs/9a02571e8f00/report_description.txt)
for an example. The base site directory (`local/site`) is configurable by the
`site_path` config parameter.

## Device Groupings

Devices can be grouped together for testing by using a "device specification"
file that is indexed by the `device_specs` configuration parameter. See
`misc/device_specs.json` for a baseline example (used for regression tests).

The basic structure is indexed by device MAC address, with a few basic fields:

* `group`: Networking group for the device, which is functionally
equivalent to a named subnet. If no <em>group</em> is specified, then it
defaults to an isolated group based on the device's MAC address. Devices in
the same group will have network reachability (sans MUD restrictions) with
a shared DHCP server (et. al.), while devices in separate groups will be
completely sequestered.
* `type`: The type of device, used for indexing into an appropriate MUD
file. If no <em>type</em> is specified, then it defaults to <em>default</em>
and the corresponding `mud_files/default.json` MUD file. This value is
used at runtime to index a device into a MUD file based on its MAC address.
See the [MUD ACL documentation](mudacl.md) for a more detailed description
of how MUD files are applied.

All devices in the same _group_ share a common network space, while devices in
separate (or unspecified) groups are completely disjoint. On startup, the system
will wait for _all_ devices in a group to be present before starting. To limit
communication between devices, rather than complete sequestering, they must
be in the same group and have compatible _type_ parameters applied.

## Device Topologies

Specific flows can be setup between devices using a specification like the example
in [device_specs_bacnet_star.json](../misc/device_specs_bacnet_star.json). Devices
(specified by MAC addresses) can be linked together through their corresponding
MUD files. For example, the existence of the JSON path object:

`macAddrs.9a:02:57:1e:8f:01.controllers.bacnet.controlees.bacnet.mac_addrs.9a:02:57:1e:8f:02`

Implies that the device :01 is linked to device :02 by the `bacnet` 'controllers' in their
corresponding MUD files, as specified by their type: The
[MUD file for type `bacnet`](../mud_files/bacnet.json) has multiple `"controller": "bacnet"`
entries that correspond to the protocol/port combinations that should be allowed.
