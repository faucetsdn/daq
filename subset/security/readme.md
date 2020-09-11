# Security testing

## test_tls
The TLS test attempts to verify various versions of TLS support.  Separate connections will be attempted with different SSL context with the associated TLS support, 1.0, 1.2 and 1.3 to teset devices server TLS capabilities.  A 5 min max scan period is also used to capture TLS client level capabilities for TLS 1.2 and 1.3.
 
### Testing procedure for server testing
After establishing connections to devices, the test will proceed to validate the available certificates with the following criteria:
 1. The certificate is in the x509 format
 2. The public key length is at the correct bit length
    - If public key is RSA format - Key length must be at least 2048
    - If public key is EC format - key length must be at least 224
 3. The certificate is not expired and active for the current date
 4. The cipher suite is valid:(only for TLS < 1.3)
    - If RSA public key format - No cipher check is required
    - If EC pubic key format - Check if cipher suites ECDH and ECSA are present
5. The certificat is signed by a CA.  This can be a local CA from the manufacturer and does not require an official CA signature.

### Testing procedure for client testing
A 5 minute maximum scan period is utilized to analyze outbound traffic from the device.  A thirty second wait period between scans is utilized to allow for early completion of the test and not require the full 5 minutes if possible. The results expec the following criteria to pass for TLS 1.2 and 1.3 success.

1. Device initiates handshake on ports 443(HTTPS) or 8883 (MQTT)
2. Server completes the handshake
3. Device is supports ECDH and ECDSA ciphers.  Only checked for TLS 1.2

### Note for test developers 
The functional test code is included in the `tlstest/src/main/java` folder

### Available Configurations:
The tls test requires specifying the CA certificate used to sign the signature for validation. If this is not added, DAQ will still run the test but will always show failure results for the server tests. To do this, you need to add the name of the ca_file to the modules section of the device config_module.json.  See the below example:
```
  "modules": {
    "tls": {
      "ca_file": "ca.pem"
    }
  }
```
The file must be loaded into the aux directory of the device, i.e local/site/mac_addres/<mac>/aux/ca.pem

 ### Conditions for security.tls.v1.server
 - pass -> If the device responds to a connection with TLS 1.0, support and provides a valid certificate, has a valid key length and has a valid cipher suite.
 - fail -> If the device responds to a connection with TLS 1.0 support and provides an invalid certificate or provides an invalid key length or an invalid cipher suite.
 - skip -> If no connection to the device can be established.

 ### Conditions for security.tls.v1_2.server
 - pass -> If the device responds to a connection with TLS 1.2, support and provides a valid certificate, has a valid key length and has a valid cipher suite.
 - fail -> If the device responds to a connection with TLS 1.2 support and provides an invalid certificate or provides an invalid key length or an invalid cipher suite.
 - skip -> If no connection to the device can be established.

 ### Conditions for security.tls.v1_3.server
 - pass -> If the device responds to a connection with TLS 1.3, support and provides a valid certificate and has a valid key length.
 - fail -> If the device responds to a connection with TLS 1.3 support and provides an invalid certificate or provides an invalid key length.
 - skip -> If no connection to the device can be established.
 
 ### Conditions for security.tls.v1_2.client
 - pass -> If the device makes a TLS 1.2 connection to an external server and the server completes the handshake. The device must support the ECDH and ECDSA cipher suites during the handshake.
 - fail -> If the attemps to make a TLS 1.2 connection to an external server and the server does not complete the handshake or if the handshake does not includes the ECDH and ECDSA cipher suite support. 
 - skip -> If no TLS 1.2 device initiated connection can be detected.
 
  ### Conditions for security.tls.v1_3.client
 - pass -> If the device makes a TLS 1.3 connection to an external server and the server completes the handshake.
 - fail -> If the attemps to make a TLS 1.3 connection to an external server and the server does not complete the handshake.
 - skip -> If no TLS 1.3 device initiated connection can be detected.

 
## test_password
The password test runs a dictionary brute force on protocols HTTP, HTTPS, SSH and Telnet to check if the device has changed login credentials from defaults to a more secure combination.

### Testing Procedure:
1. Use Nmap tool to check if needed port is open, and whether the target host is down.
2. If target port is open, and target host is not down, then start the brute force.
3. Run the brute force command for ncrack/medusa as appropriate, and collect the output.
4. Depending on the messages read on the command output, the test will return a specific result case.
 - PASS: Test was able to run the brute force but not find the username/password(s).
 - FAIL: Test was able to run the brute force and find the username/password(s).
 - SKIP: Test was not able to run a brute force successfully due to a variety of issues. In this case:
   - Target host is down.
   - Target protocol is down.
   - HTTP server does not have authentication.
   - Brute force tool related issues such as disconnect, missing parameters etc.
   
### Available Configurations:
The password test can be run from DAQ without specifying any further configurations, but it is possible to tweak these to your needs by modifying the password field in your local copy of module_config.json to have the following, for example:

Note the examples shown are the available configurations and the default values used by the password test.
```
# local/module_config.json
{
  "device_info": {
    # Both must be specified for these to be used. Should not be the default value/null/empty string. Spaces and colons are automatically removed.
    "default_username": "*** (optional) ***",  # If specified, only uses this to brute force. 
    "default_password": "*** (optional) ***"  # If specified, only uses this to brute force.
  },
  "modules": {
    "password": {
      "enabled": true,
      "dictionary_dir": "resources/default",  # Default are resources/default (full), or resources/faux (debug), user can also create their own custom version.
      "http_port": 80,  # Custom port to use when brute forcing HTTP
      "https_port": 443,  # Custom port to use when brute forcing HTTPS
      "ssh_port": 22,  # Custom port to use when brute forcing SSH
      "telnet_port": 23  # Custom port to use when brute forcing Telnet
    }
  }
}
```

Ideally one should specify only either "default_username" and "default_password" OR "dictionary_dir" - If both are specified, the default username/passwords will take precedence and dictionary_dir will be used as a backup if they are considered invalid.

## test_ssh
The SSH test will check that if a device has an SSH server, this only supports SSHv2

### Conditions for seucrity.ssh.version
- pass -> If the device runs an SSH server which only supports SSHv2
- fail -> If the device runs an SSH server which supports SSHv1
- skip -> If the device does not run an SSH server
