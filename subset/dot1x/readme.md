# 802.1x Test

## Overview
- The dot1x module provides a:
   - 802.1x authenticator, which runs during the module
   - radius server (FreeRadius)
- The authenticator only runs while the dot1x test module is running (it will
  not be running during the startup or other test modules)
- The authenticator listens to EAPOL-Start packets sent from a supplicant on a
  device. If any are received, it will respond with the EAP-RequestIdentity
  packet, and continue the 802.1x authentication process

## Tests

### connection.dot1x.authentication

#### Test Description
This tests validates general support for 802.1x authentication by testing that a device
can authenticate using 802.1x with one of the following supported protocols:
- TTLS
- TLS
- PEAP/MSChapv2
- MD5

The test is run by configuring the device to use one of the provided 
credentials included in this test module. 

#### Supported Protocols/Supplicant Credentials
The module includes a set of credential which should be used to configure the device.

Certificates are located in the 
[resources/802.1x/cert](../../resources/802.1x/cert) directory. 

Different suppliants may use different names for the below fields or may not
provide the ability to modify all these fields. 
- **TTLS**
   - Username: `user`
   - Password: `microphone`
   - CA Certificate: [ca.pem](../../resources/802.1x/cert/ca.pem)
   - Inner (Phase 2) Authentication: MSCHAPV2
- **TLS**
   - Identity: `user@example.org`
   - CA Certificate: [ca.pem](../../resources/802.1x/cert/ca.pem)
   - Client Certificate: [user@example.org.pem](../../resources/802.1x/cert/user@example.org.pem)
   - Private Key: [user@example.org.pem](../../resources/802.1x/cert/user@example.org.pem)
   - Private Key Password: `whatever`
- **Protected EAP (PEAP)**
   - CA Certificate: [ca.pem](../../resources/802.1x/cert/ca.pem)
   - Outer (Phase 1) Authentication: PEAP Version 1
   - Inner (Phase 2) Authentication: MSCHAPV2
   - Username: `user`
   - Password: `microphone`
- **MD5**
   - Username: `user`
   - Password: `microphone`

### Result Cases
- PASS: The device successfully authenticates using 802.1x 
- Fail: The device could not successfully authenticate using 802.1x. Reasons could be:
    - Invalid credentials or configuration
    - Device did not respond to EAP packets
- SKIP: Device did not send any EAP packets (likely does not support 802.1x or not configured for 802.1x)
