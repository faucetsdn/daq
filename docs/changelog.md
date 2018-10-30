# Changelog

* 0.8.0
	* Dynamic application of MUD files.
	* Pull network topology from faucet.yaml file.
* 0.8.1
	* Refactor gateway component out from individual device tests.
	* Move more configuration to faucet.yaml files.
	* Enable device groups.
	* Clean up testing infrastructure.
* 0.8.2
	* Update to use python3 (may require bin/clean for local setups).
	* Adding docs for test lab setup.
	* Improvements to docker test stability.
	* Purge old docker containers after new image download.
	* MUD file generator error message improvements.
	* Add -n (no_test) mode to just put devices on network.
	* Make cmd/run behavior configurable (in- or ex- to container).
	* Preliminary schema validation capability.
* 0.8.3
	* Upload test report to a cloud storage bucket included in web page.
	* Bug fixes for startup pcap capture.
	* Minor debugging output improvements.
	* MUD file generator 'controller' capability.
	* Documentation updates: topology, firebase, validator, debugging.
	* Updated FAUCET to version 1.8.25.
* 0.9.0
	* Upping major version number because of breaking config changes.
	* Updating schema validator code structure.
	* Improved internal checks on startup sequence.
	* Autogenerate faucet.yaml file, rather than relying on template.
