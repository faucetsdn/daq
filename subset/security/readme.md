# Security testing

## test_tls
The TLS test attempts to verify various versions of TLS support.  Separate connections will be attempted with different SSL context with the associated TLS support, 1.0, 1.2 and 1.3.
 
### Testing procedure
After establishing connections to devices, the test will proceed to validate the available certificates with the following criteria:
 1. The certificate is in the x509 format
 2. The public key length is at least 2048.  Currently handles both RSA and DSA public key formats.
 3. The certificate is not expired and active for the current date.
The cipher suite used is also checked but does not currently affect the outcome of the results.  Currently the expected cipher suites are ECDH and ECSA.  If these are not present, a warning message will be logged in the activate.log of the switch node.

 
### Note for test developers 
The functional test code is included in the `tlstest/src/main/java` folder.

 ### Conditions for security.tls.v1
 - pass -> If the device responds to a connection with TLS 1.0 support and provides a valid certificate.
 - fail -> If the device responds to a connection with TLS 1.0 support and provides an invalid certificate.
 - skip -> If no connection to the device can be established.

### Conditions for security.tls.v1.x509
 - pass -> If the device responds to a connection with TLS 1.0 support and provides a valid certificate.
 - fail -> If the device responds to a connection with TLS 1.0 support and provides an invalid certificate.
 - skip -> If no connection to the device can be established.

### Conditions for security.tls.v1_2
 - pass -> If the device responds to a connection with TLS 1.2 support and provides a valid certificate.
 - fail -> If the device responds to a connection with TLS 1.2 support and provides an invalid certificate.
 - skip -> If no connection to the device can be established.

### Conditions for security.tls.v1_2.x509
 - pass -> If the device responds to a connection with TLS 1.2 support and provides a valid certificate.
 - fail -> If the device responds to a connection with TLS 1.2 support and provides an invalid certificate.
 - skip -> If no connection to the device can be established.
 
### Conditions for security.tls.v1_3
 - pass -> If the device responds to a connection with TLS 1.3 support and provides a valid certificate.
 - fail -> If the device responds to a connection with TLS 1.3 support and provides an invalid certificate.
 - skip -> If no connection to the device can be established.

### Conditions for security.tls.v1_3.x509
 - pass -> If the device responds to a connection with TLS 1.3 support and provides a valid certificate.
 - fail -> If the device responds to a connection with TLS 1.3 support and provides an invalid certificate.
 - skip -> If no connection to the device can be established.
 
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
