# Faux device

The _faux_ device represents a reference design for a Device Under Test that can
be configured to emulate { _pass_, _fail_, _skip_ } modes for most tests. It
consists of a docker container or two (in `docker/`) and the `misc/start_faux` file.

Unless there's a specific reason it can't be done (e.g. hardware requirements), all tests
should have a _pass_ and _fail_ condition in the faux device (and also possibly _skip_),
so that the basics of any test can be validated. E.g., for DHCP, it can be configured
to do DHCP properly, to have an excessively long lease renew time, or not to DHCP at all.
Although tests ultimately run againt physical hardware (the device under test), it's a
core software engineering foundation to have a solid integration test environment.

## Executing Container

Creating a faux device means running the _faux_ Docker container that is connected to
the rest of the system by a network interface. This interface can then be used to
connect the device into various DAQ setups. The basic execution of the faux device
uses the `cmd/faux` command with a variety of command line arguments.

* `cmd/faux`: Baseline faux image.
* `cmd/faux 1`: Creates faux image #1, allowing for multiple simultanous instances.
* `cmd/faux :eth238ea8`: Instantiate using an already existing network interface.
* `cmd/faux tls`: Configure for 'tls' mode (run servers internally as appropriate).
* `cmd/faux alt`: Use the alternate faux image (_faux2_ rather than _faux1_).
* `cmd/faux 2 alt tls xdhcp`: Run instance #2 using the alternate image with both the
_tls_ and _xdhcp_ options.

## Faux Testing

A faux image can be tested by using the `bin/test_module` command, which specifically
tests one test module against a faux image. This is the easiest way to develp/test
anything to do with a faux container (or test module) since it does not involve the
entire DAQ framework. See [module test instructions](module_test.md) for me details.

## External Patching

An external network interface can be used to test the faux device against an external
switch. To do this, simply pass the name of the network interface to the faux module,
and wire it up externally as desired. E.g., `cmd/faux :eth238ea9` will create a faux
device using the `eth238ea9` network interface. This does not need to be on the same
machine as DAQ itself, so can be used for more controlled test setups.
