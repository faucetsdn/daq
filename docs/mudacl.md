## MUD ACL generator prototype

The MUD ACL generator prototoype combines MUD files with a currently static set of system configuration
files to produce FAUCET-compatible ACLs. This feature is in the early stages, so some assembly is
required. Specifically, as a development feature, the system will need to be setup for running in
development mode (see [build documentation](build.md)). Everything here is subject to change.
Initially, this only provides a limited subset of
policy enforcement; additional restrictions will manifest as the system improves.

The basic combinator application (invoked with `bin/mudacl`) combines the following pieces of information:

* <b>Switch Topology</b>: Specified by `inst/faucet.yaml` (shouldn't need to change).
* <b>Device Topology</b>: Specified in `local/devices.json` (copied into place by `bin/mudacl`).
* <b>Device Types</b>: Specified in `local/types.json` (copied into place by `bin/mudacl`).
* <b>MUD Files</b>: Specified in `mud_files/`.

The `bin/mudacl` script will output compiled results into `inst/port_acls/`, where they are then
included by the FAUCET runtime (see include directives in `inst/faucet.yaml`).

The following steps show how it all works for a test against the internal faux device. Just requires
a simple edit to the default `system.conf` file to enable some deviant device behavior. First it runs
DAQ without MUD, showing the exposed telnet port, and then again with MUD enforcement which should not
allow telnet.

```
~/daq$ diff misc/system.conf local/system.conf
13c13
< #faux_args="telnet"
---
> faux_args="telnet"
~/daq$ sudo rm -rf inst/port_acls inst/faucet.log
~/daq$ sudo cmd/exrun -s > daq_open.log 2>&1
~/daq$ fgrep port_1_acl inst/faucet.log
Jul 24 22:19:30 faucet.config WARNING  not a regular file or does not exist: /etc/faucet/port_acls/dp_sec_port_1_acl.yaml
Jul 24 22:19:30 faucet.config WARNING  skipping optional include file: /etc/faucet/port_acls/dp_sec_port_1_acl.yaml
~/daq$ cat inst/run-port-01/nodes/nmap01/tmp/open.txt
23/open/tcp//telnet///
~/daq$ bin/mudacl
touch: setting times of 'inst/': Permission denied
BUILD SUCCESSFUL in 1s
2 actionable tasks: 2 up-to-date
Executing mudacl generator...
Writing output files to /home/username/daq/inst/port_acls
total 8
-rw-rw-r-- 1 username username 939 Jul 24 22:21 dp_sec_port_1_acl.yaml
-rw-rw-r-- 1 username username 518 Jul 24 22:21 dp_sec_port_2_acl.yaml
~/daq$ sudo rm inst/faucet.log
~/daq$ sudo cmd/exrun -s > daq_mud.log 2>&1
~/daq$ fgrep port_1_acl inst/faucet.log
~/daq$ cat inst/run-port-01/nodes/nmap01/tmp/open.txt
~/daq$ 
```
