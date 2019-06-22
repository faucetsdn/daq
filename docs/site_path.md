# Site path configuration

The `site_path` configuration variable determines where site-specific information is stored.
This is different than `local/` which is always local to the physical machine. The site path
would ideally be stored in a git repo (separate from DAQ), that can then be used to share
configuraiton across installs. The site path defaults to `local/site`, which means you can
also store your entire configuraiton of local/ in the same source control repo, if desired.

# Module configs

A test module config is constructed for each test from a sequence of overlaid files. The
general sequence of includes is:

* `misc/module_config.json`: Global configuraiton paramaters that come with the DAQ distribution.
* `{site_path}/module_config.json`: Confguraiton parameters common to all tests run with this site.
* `{site_path}/device_types/{device_type}/module_config.json`: Device-type configuration parameters.
* `{site_path}/mac_addrs/{mac_addr}/module_config.json`: Device-specific configuraiton parameters.
* `{test_config}/port-{port}/module_config.json`: Switch-port specific configuration parameters.

The `device_type` is optionally specified in the device-specific configuration file (even
though the device file is merged later). The `port` designaton will be something like `02` for
port 2 (so `/port-02/` in the path).

The merged config file is written to `{site_path}/mac_addrs/{mac_addr}/aux/module_config.json`
and is available to a test container at runtime (along with all the other files in the `aux`
directory).

# Configuration parameters

* Each test can be enabled or disabled at any level, see this
[site level example](https://github.com/faucetsdn/daq/blob/master/misc/test_site/module_config.json) uner the `modules` section.
* Generic test options are also possible, but the exact contents depend on the tests themselves. See this
[device level example](https://github.com/faucetsdn/daq/blob/master/misc/test_site/mac_addrs/9a02571e8f01/module_config.json)
for how to "allow" certain ports under the `servers` section.
* Many other parameters (seen in the examples) are simply passed through to the generated report.

# Web UI

There are also ways to edit both _site_ and _device_ configs directly through the WEB UI. Currently the
documentation for that is not available, but some people on the mailing list know how to do it.
