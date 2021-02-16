# Site path configuration

The `site_path` configuration variable determines where site-specific information is stored.
This is different than `local/` which is always local to the physical machine. The site path
would ideally be stored in a git repo (separate from DAQ), that can then be used to share
configuration across installs. The site path defaults to `local/site`, which means you can
also store your entire configuration of local/ in the same source control repo, if desired.

For initial testing and setup, setting `site_path=resources/test_site` will use the default devices
used for integration testing and is a good way to get started.

# Module configs

A test module config is constructed for each test from a sequence of overlaid files. The
general sequence of includes is:

* `resources/setups/baseline/base_config.json`: Global configuration parameters that come with the DAQ distribution.
* `{site_path}/site_config.json`: Configuration parameters common to all tests run with this site.
* `{site_path}/device_types/{device_type}/type_config.json`: Device-type configuration parameters.
* `{site_path}/mac_addrs/{mac_addr}/device_config.json`: Device-specific configuration parameters.
* `{test_config}/port-{port}/port_config.json`: Switch-port specific configuration parameters.

The `device_type` is optionally specified in the device-specific configuration file (even
though the device file is merged later). The `port` designaton will be something like `02` for
port 2 (so `/port-02/` in the path).

The merged config file is written to `{site_path}/mac_addrs/{mac_addr}/aux/module_config.json`
and is available to a test container at runtime (along with all the other files in the `aux`
directory).

![Diagram](module_config.png)

# Configuration parameters

* Each test can be enabled or disabled at any level, see this
[site level example](https://github.com/faucetsdn/daq/blob/master/resources/test_site/site_config.json) under the site section.
* Generic test options are also possible, but the exact contents depend on the tests themselves. See this
[device level example](https://github.com/faucetsdn/daq/blob/master/resources/test_site/mac_addrs/9a02571e8f01/device_config.json)
for how to "allow" certain ports under the `servers` section.
* Many other parameters (seen in the examples) are simply passed through to the generated report.

## Test configuration

See `resources/test_site/site_config.json` for an example of line-item test configurations,
which should look something like:
```
{
  "tests": {
    "security.ports.nmap": {
      "required": "pass",
      "category": "Security",
      "expected": "Recommended"
    }
  }
}
```

All fields are optional.

* `required`: The required test result, which normally would be `pass` but could be any other
test result. The presence of this field means that it must match the actual test result
in order for the device to pass overall. A _required_ test entry will always be tracked
in the report, even if no module implements it (using the sekrit `gone` result).
* `category`: The test category, which is used to accumulate tests into top-level groups. There is
no semantic meaning to this value.
* `expected`: The expected state of this test, which is purely informational and again used to bucket
test results (just in a different way). There is no semantic meaning to this value.

# Web UI

There are also ways to edit both _site_ and _device_ configs directly through the WEB UI. Currently the
documentation for that is not available, but some people on the mailing list know how to do it.
