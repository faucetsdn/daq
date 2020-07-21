# Security testing

## test_tls
The TLS test attempts to verify various versions of TLS support.  Separate connections will be attempted with different SSL context with the associated TLS support, 1.0, 1.2 and 1.3.
 
 ### Testing procedure
 After establishing connections to devices, the test will proceed to validate the available certificates with the following criteria:
 1. The certificat is in the x509 format
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

## test_ssh
The SSH test will check that if a device has an SSH server, this only supports SSHv2

### Conditions for seucrity.ssh.version
- pass -> If the device runs an SSH server which only supports SSHv2
- fail -> If the device runs an SSH server which supports SSHv1
- skip -> If the device does not run an SSH server