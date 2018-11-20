## MUD ACL Generator Prototype

The MUD ACL generator prototoype combines
[IETF MUD files](https://datatracker.ietf.org/doc/draft-ietf-opsawg-mud/)
with the dynamic state of the system to produce FAUCET-compatible network ACLs.
This feature is in the early stages, so some assembly is
required. Specifically, as a development feature, the system will need to be setup for running in
development mode (see [build documentation](build.md)). Everything here is subject to change.
Initially, this only provides a limited subset of
policy enforcement; additional restrictions will manifest as the system improves.

The basic combinator application (invoked with `bin/mudacl`) processes the set of MUD files
contained in the directory specified by the `mud_files` config parameter (defaults to `mud_files/`)
and generates a set of ACL templates in `inst/acl_templates`. To work with a custom set of MUD files,
edit `local/system.conf` and specify a different `mud_files` source directory, e.g. `local/test_devices/`.

The `device_specs` configuration entry in `system.conf` specifies a mapping for individual devices
to various dynamic runtime behavior. See the
[device specs documentation](device_specs.md) for more details.
If this file is not specified, then no flow restrictions will be enforced
(outside of the detailed group-based restrictions).

The following steps show how it all works for a test against the internal faux device. Just requires
a simple edit to the default `system.conf` file to enable some deviant device behavior. First it runs
DAQ without MUD, showing the exposed telnet port, and then again with MUD enforcement which should not
allow telnet.

<pre>
<b>~/daq$</b> diff local/system.conf misc/system_base.conf
7c7
< daq_intf=faux-1!
---
> daq_intf=faux!
13c13
< faux_args="telnet"
---
> #faux_args="telnet"
<b>~/daq$</b> sudo rm -rf inst/port_acls inst/device_types.json
<b>~/daq$</b> sudo cmd/run -s > daq_open.log 2>&1
<b>~/daq$</b> fgrep template daq_open.log
<b>~/daq$</b> cat inst/run-port-01/nodes/nmap01/tmp/open.txt
23/open/tcp//telnet///
<b>~/daq$</b> bin/mudacl

BUILD SUCCESSFUL in 0s
2 actionable tasks: 2 up-to-date

Executing mudacl generator...
Writing output files to /home/username/daq/inst/acl_templates
-rw-r--r-- 1 username primarygroup  140 Jul 31 15:38 inst/device_types.json

inst/acl_templates:
total 16
-rw-r--r-- 1 username primarygroup 408 Jul 31 15:38 template_baseline_acl.yaml
-rw-r--r-- 1 username primarygroup  44 Jul 31 15:38 template_default_acl.yaml
-rw-r--r-- 1 username primarygroup 465 Jul 31 15:38 template_lightbulb_acl.yaml
-rw-r--r-- 1 username primarygroup 217 Jul 31 15:38 template_telnet_acl.yaml

inst/port_acls:
total 0
<b>~/daq$</b> ls -l inst/device_types.json
-rw-r--r-- 1 username primarygroup 140 Jul 31 15:38 inst/device_types.json
<b>~/daq$</b> sudo cmd/run -s > daq_mud.log 2>&1
<b>~/daq$</b> fgrep template daq_mud.log
INFO:network:Processing acl template for 9a:02:57:1e:8f:01/lightbulb
<b>~/daq$</b> cat inst/run-port-01/nodes/nmap01/tmp/open.txt
<b>~/daq$</b>
</pre>
