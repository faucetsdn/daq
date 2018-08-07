# FAUCET Configurations Options

This describes the necessary bits and extensions to the standard
[FAUCET network configuration file](https://github.com/faucetsdn/faucet/blob/master/docs/configuration.rst)
when working with DAQ. This is not comprehensive, so either learning-by-example or a deeper understanding
of the core FAUCET system will be required.

## DAQ Core Switch

DAQ uses one core switch to control the testing dataflow. In the configuration files this is
always referenced with a dp_id of 1. The large number of interface ports is used to direct
network trafic to subsets of internal hosts (e.g. DHCP server, test program) for testing.

## Autostart Provisions

In order to streamline testing, it is possible to include autostart directives in a FAUCET config file.
These are interpreted by the DAQ system when invoked, but are not necessary for normal "production"
operation. E.g. the following line in `misc/faucet.yaml` will cause a faux-device to be created
when DAQ is started (with extra arguments specified by the environment):

```description: DAQ autostart cmd/faux $DAQ_FAUX_OPTS```
