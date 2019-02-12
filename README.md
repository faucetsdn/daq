# DAQ: <b>D</b>evice <b>A</b>utomated <b>Q</b>ualification for IoT Devices.

DAQ is a framework designed to test and operate IoT devices in an enterprise IoT environment.
Nominally about device testing and qualification, Device Automated Qualification (DAQ), provides
a means to _automate_ many capabilities, resulting in a more manageable, robust, and
secure platform.

Join the [daq-users@googlegroups.com](https://groups.google.com/forum/#!forum/daq-users) email
list for ongoing discussion about using DAQ for enterprise IoT devices.

There are several main categories of capabilities that DAQ addresses:
* [_Individual device automated qualification and testing_](docs/qualification.md):
Testing the behavior of a device against established security and network standards.
More details about the goals and objectives behind this can be found in the IEEE Computer article
[Taming the IoT: Operationalized Testing to Secure Connected Devices](https://www.computer.org/csdl/mags/co/2018/06/mco2018060090-abs.html).
* [_Network security microsegmentation flow management_](docs/mudacl.md): Use standard
[SDN capabilities](https://queue.acm.org/detail.cfm?id=2560327), such as the
[FAUCET OpenFlow controller](https://faucet.nz/), to automatically configure network to enforce
tight "microsegmentation" on the network.
* [_Universal Device Management Interface (UDMI)_](schemas/udmi/README.md): An interface
specification designed to normalize the management of IoT devices from different manufacturers.
This is a simple standard that provides for many of the common features not present in
existing protocols (e.g. BACnet).
* _Device Management Tools_: A suite of tools, consoles, and dashboards that help operate
a robust ecosystem of IoT devices. (Details forthcoming.)

## System Requirements

Most aspects of DAQ assume a baseline setup consisting of:
* Linux install: DAQ has been tested against both `Ubuntu 16.04.4 LTS xenial` and
`Debian GNU/Linux 9.4 stretch`, YMMV with other platforms.
* Dedicated network adapters: At the very minimum one dedicated ethernet adapter is
required. This could either be a separate built-in NIC, or a USB-Ethernet dongle.
* (Optional) OpenFlow-compatible hardware switch, described in the
[Network Topologies](docs/topologies.md) overview.

## Folder Structure

The top-level DAQ folders correspond to the following structure:
* `bin/`: System setup and management commands.
* _`build/`_: Dynamically created directory for build logs.
* `cmd/`: Primary commands for running DAQ testing.
* `daq/`: Python source for DAQ runtime.
* `docker/`: Docker build files for DAQ components and tests.
* `docs/`: Documentation.
* _`faucet/`_: Dynamically downloaded version of SDN controller.
* `firebase/`: Hosted pages and functions for web dashboard.
* `functions/`: Additional Cloud Functions for data processing.
* _`inst/`_: Install directory for specific runtime contents.
* **`local/`**: Local setup and config information.
* _`mininet/`_: Local version of the mininet virtual network host framework.
* `misc/`: Miscellaneous support files.
* `mudacl/`: Utilities for managing and testing MUD network files.
* `mud_files/`: Examples and prototype device MUD files.
* _`out/`_: Misc transitory output files.
* `pubber/`: Sample code for generating cloud-ingest traffic.
* `schemas/`: Device/cloud data exchange schemas.
* `subset/`: Subsets of device tests (e.g. penetration tests).
* `testing/`: Scripts for system continuous integration testing.
* `topology/`: Network topology setups.
* `validator/`: Tools for validating data exchange schemas.
* _`venv/`_: Dynamically downloaded python virtual environment files.

Items in _italics_ can generally be deleted without any loss of functionality (dynamically
created at install/runtime). The **local** subdirectory contains local setup information that
is not part of the source distribution.
