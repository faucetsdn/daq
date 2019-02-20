# Orchestration

_Orchestration_ is a sub-function of the overall DAQ framework that
enables the enforcement of network microsegmentation using the capabilities provided
by the [Faucet OpenFlow network controller](https://faucet.nz/). The system takes
in a number of device topology specification descriptiors, and dynamically applies
network-based port restrctions at runtime.

NB: The various file formats are in various stages of specification and are subject
to change.

## Data Rouces

The overal orchestration capability relies on several simple data sources:
1. [Overall network topology](topologies.md), which indicates how the network hardware is configured.
2. [Device MUD files](../mud_files), which provide an
[IETF Standard MUD descriptor](https://datatracker.ietf.org/doc/draft-ietf-opsawg-mud/) that describes
the network protocol/ports (e.g. UDP on port 47808) utilized by a device.
3. [System device topology specification](../misc/device_specs_bacnet_star.json), which indicates how
devices are interconnected.

## Sequence of Events

1. Pre-runtime, MUD file are compiled into templatized fACLs (Faucet ACLs), such as the
[BACnet ACL example](../mudacl/setup/acl_templates/template_bacnet_acl.yaml).
2. When a new device is detected (characterized by a Faucet switch learning event), the system
looks up the device's specification in the configured `device_spec`, correlating it's `type`
field with a similarly-named MUD template.
3. Templatized field information (like destination hosts) are resolved based on the current
state of the network topology.
4. The resolved fACLs are applied to the device's switch port and switch-interconnect,
effectively limiting network flows.

## Execution Example

To see how the system is configured and executed, see the integration tests defined in the
[`testing/test_topo.sh`](../testing/test_topo.sh) test script.
