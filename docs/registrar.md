# Registrar Overview

The `registrar` is a utility program that registers and updates devies in Cloud IoT.
Running `bin/registrar` will pull the necessary configuraiton values from `local/system.conf`,
build the executable, and register/update devices.

## Configuration

The `local/system.conf` file should have the following parameters (in `x=y` syntax):
* `gcp_cred`: Defines the target project and service account to use for configuration.
Can be generated and downloaded from the Cloud IoT Service Account page.
* `site_path`: Path of site-specific configuration. See example in `misc/test_site`.
* `schema_path`: Path to metadata schema (for validation).

The target `gcp_cred` service account will need the _Cloud IoT Provisioner_ and _Pub/Sub Publisher_ roles.
There also needs to be an existing `registrar` topic (or as configured in `cloud_iot_config.json`, below).

## Theory Of Operation

* The target set of _expected_ devices is determined from directory entries in
<code>_{site_path}_/devices/</code>.
* Existing devices that are not listed in the site config are blocked (as per
Cloud IoT device setting).
* If a device directory does not have an appropriate key, one will be automaticaly generated.
* Devices not found in the target registry are automatically created.
* Existing device registy entries are unblocked and updated with the appropriate keys.

## Device Settings

When registering or updating a device, the Registrar manipulates a few key pieces of device
information:
* Auth keys: Public authentiation keys for the device.
* Metadata: Various information about a device (e.g. site-code, location in the building).
* Gateway Config: A proxy-mode device's gateway settings and binding.

This information is sourced from a few key files:

* `{site_dir}/cloud_iot_config.json`:
Cloud configuration parameters (`registry_id`, `cloud_region`, etc...).
* `{site_dir}/devices/{device_id}/properties.json`:
Device-specific properties (e.g. device mode).
* `{site_dir}/devices/{device_id}/metadata.json`:
Device metadata (e.g. location).
* `{site_dir}/devices/{device_id}/rsa_private.pem`:
Generated private key for device (used on-device).

## Sample Output

<pre>
~/daq$ <b>bin/registrar</b>
Loading config from local/system.conf

> Task :compileJava 
&hellip;
BUILD SUCCESSFUL in 4s
2 actionable tasks: 2 executed
Using gcp credentials local/daq-testing-de56aa4b1e47.json
Using site config dir misc/test_site
Using schema root dir schemas/udmi
Using service account daq-laptop@daq-testing.iam.gserviceaccount.com/null
Created service for project daq-testing
Updated device entry AHU-001
Blocking extra device AHU-002
Blocking extra device bad_device
Registrar complete, exit 0
~/daq$ 
</pre>

## Sequence Diagram

Expected workflow to configure a registry using Registrar:

* `Device`: Target IoT Device
* `Local`: Local clone of site configuration repo
* `Registrar`: This utility program
* `Registry`: Target Cloud IoT Core registry
* `Repo`: Remote site configuration repo

All operations are manaul except those involving the `Registrar` tool.

<pre>
+---------+                +-------+                 +-----------+                 +-----------+ +-------+
| Device  |                | Local |                 | Registrar |                 | Registry  | | Repo  |
+---------+                +-------+                 +-----------+                 +-----------+ +-------+
     |                         |                           |                             |           |
     |                         |                           |                       Pull repo locally |
     |                         |<--------------------------------------------------------------------|
     |                         |    ---------------------\ |                             |           |
     |                         |    | Run Registrar tool |-|                             |           |
     |                         |    |--------------------| |                             |           |
     |                         |                           |                             |           |
     |                         | Read device configs       |                             |           |
     |                         |-------------------------->|                             |           |
     |                         |                           |                             |           |
     |                         |                           |            Read device list |           |
     |                         |                           |<----------------------------|           |
     |                         |                           |                             |           |
     |                         |           Write auth keys |                             |           |
     |                         |<--------------------------|                             |           |
     |                         |                           |                             |           |
     |                         |                           | Update device entries       |           |
     |                         |                           |---------------------------->|           |
     |                         |   ----------------------\ |                             |           |
     |                         |   | Registrar tool done |-|                             |           |
     |                         |   |---------------------| |                             |           |
     |                         |                           |                             |           |
     |     Install private key |                           |                             |           |
     |<------------------------|                           |                             |           |
     |                         |                           |                             |           |
     |                         | Push changes              |                             |           |
     |                         |-------------------------------------------------------------------->|
     |                         |                           |                             |           |
</pre>

### Source

Use with [ASCII Sequence Diagram Creator](https://textart.io/sequence#)

<pre>
object Device Local Registrar Registry Repo
Repo -> Local: Pull repo locally
note left of Registrar: Run Registrar tool
Local -> Registrar: Read device configs
Registry -> Registrar: Read device list
Registrar -> Local: Write auth keys
Registrar -> Registry: Update device entries
note left of Registrar: Registrar tool done
Local -> Device: Install private key
Local -> Repo: Push changes
</pre>
