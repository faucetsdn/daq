# Switch testing

## test_switch
The switch test attempts to poll the switch for different types of data as it relates to the
connected devices.

## Currently supported switches:
 - Cisco Catalyst 9300
 - Allied Telesis x230

### Default Logins:
 - Cisco Catalyst 9300:
   - User: admin
   - Password: password
 - Allied Telesis x230
  - User: manager
  - Password: friend

## Note for test developers
The functional test code is included in the `src/main/java` folder.

DAQ requires additional parameters to be defined in the Switches require a login to gain access to the data required so you must either configure your switch with the appropriate values in the system.conf.

Additionally to the parameters needed for all physical switch testing defined here: https://github.com/faucetsdn/daq/blob/master/docs/switcher.md

There are specific variables required for using the specified switch that must be added to the system.conf.:

- switch_model - Defines what swich is being used and is case sensitive.
 - CISCO_9300
 - ALLIED_TELESIS_X230

- switch_username: Defines the username to use when logging into the switch.  If this is not defined, it will use the default username defined for the switch defined by switch_model.

- switch_password: Defines the password to use when logging into the switch.  If this is not defined, it will use the default password defined for the switch defined by switch_model.

Example of all necessary parameters in the system.conf related to physical switch testing:
    # Data plane ID for the connected physical switch.
    switch_setup.of_dpid=0xabcdef1234

    # Interface name of the control-plane network.
    switch_setup.ctrl_intf=ens9

    # Interface name of the data-plane network.
    switch_setup.data_intf=enx00e04c6601a4

    # Controller OpenFlow port (defaults to 6653).
    switch_setup.lo_port=6653

    # Controller control plane IP address (and subnet).
    switch_setup.lo_addr=192.168.100.9/24

    # External switch IP address (used to verify the connection).
    switch_setup.ip_addr=192.168.100.99

    # Enable switch control-plane access.
    # Setting this causes the LOCAL_IP and SWITCH_IP env variables to be set in test containers
    switch_setup.mods_addr=192.168.100.1%d/24

    # Port of secondary (external) switch for the data-plane uplink (defaults to 7).
    switch_setup.uplink_port=12

	# Define the model of the switch to use. This parameter is required.
    switch_setup.model=CISCO_9300

	# Define the username for the switch. This parameter is optional.
    switch_setup.username=tester

	# Define the password for the switch. This parameter is optional.
	switch_setup.password=switch_p@55

    # If you're using a custom docker network bridge or hosting USI somewhere other than the DAQ machine, do the following: 
    # Define the usi url using your docker0's ip and port 5000, and re-run bin/setup_base if you're upgrading from versions before 1.9.0
    # Make sure docker's ip range doesn't conflict with that of the switch. Default docker ip range is 172.17.0.0/16. Default switch ip range is 192.168.0.0/16
    usi_setup.url=172.17.0.1:5000

## Conditions for connection.switch.port_duplex
 - pass -> If the duplex mode is detected as full
 - fail -> If the duplex mode is detected but not full or if the duplex mode cannot be detected

## Conditions for connection.switch.port_link
 - pass -> If the status of the port the device is plugged into is determined to be in a connected or "UP" state.
 - fail -> If the status of the port the device is plugged into is determined to be in a disconnected or "DOWN" state.

## Conditions for connection.switch.port_speed
 - pass -> If the speed of the port is auto-negotiated and determiend to be higher than 10 MBPS
 - fail ->If the speed of the port is determined to be <= 10MBPS

## Conditions for poe.switch.power
 - pass -> If the a PoE device is connected and power has been detected and supplied to the device.
 - fail -> If the a PoE device is connected and *NO* power has been detected and supplied to the device.  Failure also occurs if the switch reports either a faulty PoE state or is denying power to the device. This can also fail if associated power data fails to resolve correctly during switch interrogation.
 - skip -> If the PoE option is disabled in the device module_config.json or if the switch reports no PoE support.

