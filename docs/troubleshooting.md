# Tip and Tricks for DAQ Troubleshooting

## Overall System

* Join the
[daq-users@googlegroups.com](https://groups.google.com/forum/#!forum/daq-users)
mailing list, and use it as the primary source of troubleshooting.
  * If there is proprietary or contractual information involved, you can always
  email somebody directly, but will likely result in a slower response time.
* The `inst/cmdrun.log` file contains a copy of the console output from DAQ.
  * This file should be attached to communications about resolving DAQ issues.
  * It's not necessary to include the assocaited `system.conf` file, since the
  contents of that are already included.
* Make sure everything is running properly using the internal simulation setup
before tackling anything to do with external switches or physical devices.
  * `misc/system_base.conf` is likely the best place to start, as the simplest
  base configuration. This should generate *a* report for a faux device.
  * `misc/system_all.conf` is the next step, as it includes all the validated
  built-in tests with DAQ. This should include more tests & faux devices.
  * See [test lab setup](test_lab.md) setup for additional tips & tricks in
  dealing with external/physical switches.
* The final output of DAQ is the generated "`report.md`" file, that includes
a summary of all test results.
  * Generally found in <code>inst/reports/report_<em>XXXXX</em>.md</code> where
  <code><em>XXXXX</em></code> is some complicated unique string (e.g. MAC
  address and timestamp).
  * If this file is not present, then something is wrong with the base setup,
  please follow the previous troubleshooting steps.
  * The determination of _PASS_ vs. _FAIL_ is one of policy, not a technical
  consideration. If the question is "Is it OK if this tests fails or not?" then
  you need to contact whomever is responsible for policy, not DAQ-proper.
  * The reports are _optionally_ available trough the _optionally_ configured
  GCP instance, but that's only relevant after the basics are working.
* Capturing a complete zip of the `inst/` directory should encompass all the
state neesary to diagnose/debug problems, so simply captuing that and sending
it along would be sufficient in most cases. Be wary of file size, as `inst/`
can collect cruft over time and occasionally need to be cleaned.

## Test-Specific

For a specific test (e.g. _bacnet compliance_) here's the general sequence and
structure of data. There is no one-size-fits-all diagnostics for tests, since
each module has its own code and requirements; however, there is a common
structure for where log and diagnostic information is located. In addition to
the common `cmdrun.log` file, the test-specific `activate.log`,
`module_config.json`, and `report.txt` are the most helpul for
diagnostics and troubleshooting.

* Each test result (e.g. _protocol.bacnet.version_) is supplied by a _module_.
  * There is no obvious mapping from _test_ to _module_, so there might be
  some sleuthing involved.
* Make sure the test's _module_ is properly configured/run in the `cmdrun.log`
file.
  * E.g. for the _bacext_ module, there will be things like `Target port 3 test
  bacext running`.
* Individual test results/diagnostics can be found in a dedicated test run
directory.
  * While troubleshooting, generally advised to use the `-s` option to
  `cmd/run`. Each new test run wipes out the previous set of results.
  * Results are organized by switch port in
  <code>inst/run-port-<em>XX</em>/</code>, where <code><em>XX</em></code> is
  the device's switch port (physical or virtual).
    * Within that directory, the <code>scans/</code> subdirectory:
      * `startup.pcap`: Packet capture from startup (pre-DHCP).
      * `monitor.pcap`: Packet capture from monitoring (post-DHCP, pre-test).
    * Individual test modules are sorted in the `nodes/` subdirectory:
      * In <code><em>moduleXX</em>/</code> (module name and port number),
      e.g. `bacext02`:
        * `activate.log`: Test module activation log (docker container)
        * `tmp/`: Test module runtime directory, volume mapped into `/tmp`
        in the test module container:
          * `module_config.json`: File supplied _to_ the test module about
          configuration information (test options, etc...)
          * `report.txt`: Test results _from_ the test module, generated at
          run time and contain all the relevant test results and diagnostics.
  * If the logs don't provide the necessary information, then a wire-line
  packet capture may be in order.
    * Use something like
    <code>tcpdump -eni <em>XXXXXX</em> -w testing.pcap</code>, where
    <code><em>XXXXXX</em></code> is the data-plane network interface between
    the device and DAQ host, while the tests are running.
    * Filter results for the device's MAC address with something like:
    <code>tcpdump -en -r testing.pacp ether host <em>de:vi:ce:ma:ca:dr</em></code>.
    * There is no one-size-fits-all guidance here, because what is expected is
    extremeley test-specific.
