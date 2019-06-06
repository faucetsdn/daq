# UDMI Technology Stack

The complete UDMI specificaiton (super set of the base schema), specifies a complete
technology stack for compliant IoT devices.

# Core Requirements

* [Google Cloud's MQTT Protocol Bridge](https://cloud.google.com/iot/docs/how-tos/mqtt-bridge).
  * This is _not_ the same as a generic MQTT Broker, but it is compatible with standard client-side libraries.
  * Other transports (non-Google MQTT, CoAP, etc...) are acceptable with prior approval.
  * Connected to a specific Cloud IoT Registry designated for each site-specific project.
* Utilizes the MQTT Topic table listed below.
* JSON encoding folowing the core [UDMI Schema](README.md), specifying the semantic structure of the data.
* Passes the [DAQ Validation Tool](../../docs/validator.md) for all requirements.

# MQTT Topic Table

| Type     | Category | subFolder |                MQTT Topic              |  Schema File  |
|----------|----------|-----------|----------------------------------------|---------------|
| state    | state    | _n/a_     | `/devices/{device_id}/state`           | state.json    |
| config   | config   | _n/a_     | `/devices/{device-id}/config`          | config.json   |
| pointset | event    | pointset  | `/devices/{device-id}/events/pointset` | pointset.json |
| logentry | event    | logentry  | `/devices/{device-id}/events/logentry` | logentry.json |

# Certificate Requirements

For device 802.1x certificates (network authentication, _not_ Cloud IoT authentitation), the following
guidelines apply:

* MUST support 802.1X-2004 with authentication using EAP-TLS standard.
* Credentials for EAP-TLS should conform to X.509v3.
* Key types MUST support a minimum of RSA at minimum bit length of 2048.
* Key types ideally support ECDH and ECDSA as well at a minimum bit length of 224.
* Owner identity keys and certificates MUST be rotatable, ideally via API method and with fallback to previous credential in case rotation fails.
* Vendor supplied device specific identity keys and certificates may be static, but only if owner identity credentials are possible.
* Ideally supports 802.1X-2010, 802.1AR and 802.1AE (MACSEC) for devices that will be placed in high-risk environments (outside, and public areas).
