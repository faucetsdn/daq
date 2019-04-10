# Changelog

* Next Release:
        * Device-level test configuration (e.g. allowed open ports)
* 0.9.6:
	* UDMI Tech Stack definition (MQTT + JSON + UDMI).
	* Updating BacNET tests to have more predictable/regular identifiers.
	* Generate markdown-based reports in site device folder.
	* Registrar tool for cloud-based device registration.
	* Debian Stretch setup/install fixes.
	* Update to Faucet 1.9.1.
* 0.9.5
	* DAQ_TARGETS env variable for incremental builds.
	* Report file cleanup, with embedded test results.
	* DHCP long switchover and dhcp request logs.
	* Updating python package versions.
	* Forced workaround delay for faucet config change race-condition.
	* Faucet performance fix for large port counts.
	* Fix internal lint checks.
	* Faux command uses explicit interface designation.
	* Faux command does not rename explicit interface.
* 0.9.4
	* Faucet update to 1.8.35
	* Move device configuration data under `site_path` parameter.
	* Switch-based tests (port errors, port negotiation)
* 0.9.3
	* Device description capability for report generation.
	* Fixes for broken local_switch setup and docs.
	* Build and release documentation updates.
	* Dual stacking topology tests.
	* Port debounce feature for flaky ports.
	* Updates to FCU example status messages.
	* Debugging fail_hook setting.
	* Faucet update to version 1.8.34.
* 0.9.2
	* Stacking topology generator.
	* SWITCH_PORT env variable available to tests.
	* Automatic detection of re-build required.
	* Topology test for "commissioning".
	* Stability improvements for network topology tests.
* 0.9.1
	* Adding test_config option for dynamic test configurations.
	* Enforce gateway test group isolation.
	* Issue a representative FCU example for UDMI encodings.
	* Bacnet topology tests (open, single, halves, star)
	* Mock-switch capability for direct-to-switch tests.
	* Bacnet4j version updates for looped discovery tests.
	* Packet capture files for gateways and individual tests.
	* General improvements to system test stability.
	* Brute-force telnet password checks.
	* Update Faucet version to 1.8.32.
	* Increased MUD-file enforcement (to-device).
	* Misc build issues for current Debian/Ubuntu systems.
* 0.9.0
	* Upping major version number because of breaking config changes.
	* Updating schema validator code structure.
	* Improved internal checks on startup sequence.
	* Autogenerate faucet.yaml file, rather than relying on template.
* 0.8.3
	* Upload test report to a cloud storage bucket included in web page.
	* Bug fixes for startup pcap capture.
	* Minor debugging output improvements.
	* MUD file generator 'controller' capability.
	* Documentation updates: topology, firebase, validator, debugging.
	* Updated FAUCET to version 1.8.25.
* 0.8.2
	* Update to use python3 (may require bin/clean for local setups).
	* Adding docs for test lab setup.
	* Improvements to docker test stability.
	* Purge old docker containers after new image download.
	* MUD file generator error message improvements.
	* Add -n (no_test) mode to just put devices on network.
	* Make cmd/run behavior configurable (in- or ex- to container).
	* Preliminary schema validation capability.
* 0.8.1
	* Refactor gateway component out from individual device tests.
	* Move more configuration to faucet.yaml files.
	* Enable device groups.
	* Clean up testing infrastructure.
* 0.8.0
	* Dynamic application of MUD files.
	* Pull network topology from faucet.yaml file.
