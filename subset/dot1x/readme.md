# 802.1x Test

## Overview
- The dot1x module provides a:
   - 802.1x authenticator, which runs during the module
   - radius server (FreeRadius)
- The authenticator only runs when the dot1x is running
- The authenticator listens to EAP-Start packets sent from a supplicant on a
  device. If any are recieved, it will communicate with the device and radius
  server

## Tests

### connection.dot1x.authentication

#### Test Description
This tests validates general support for 802.1x authentication by testing that a device
can authenticate using 802.1x with one of the following supported protocols:
- TTLS
- TLS
- PEAP/MSChapv2
- MD5

#### Supported Protocols/Supplicant Credentials
The module includes a set of credentials which should be the device/supplicant
should be configured to use. These are located
[here](docker/include/etc/wpasupplicant). Different suppliants may use different
names for the below fields or may not provide the ability to modify all these
fields. 
- **TTLS**
   - EAP: TTLS
   - identity="user"
   - CA Certificate: Upload `/etc/wpasupplicant/cert/ca.pem`
   - password="microphone"
   - phase2="auth=MSCHAPV2"
   - eapol_flags=0
- **TLS**
   - EAP: TLS
   - Identity/Username: "user@example.org"
   - CA Certificate: Upload `/etc/wpasupplicant/cert/ca.pem`
   - client_cert: Upload file `/etc/wpasupplicant/cert/user@example.org.pem`
   - Private Key: Upload file `/etc/wpasupplicant/cert/user@example.org.pem`
   - Private Key Password: `whatever`
   - eapol_flags=0
- **PEAP/MSChapv2**
   - EAP:PEAP
   - ca_cert="/etc/wpasupplicant/cert/ca.pem"
   - Phase 1 Authentication: "peaplabel=1"
   - Phase 2 Authentication: auth=MSCHAPV2"
   - identity: `user`
   - password: `microphone`
- **MD5**
   - eap=MD5
   - identity: `user`
   - password: `microphone`

### Result Cases
- PASS: The device successfully authenticates using 802.1x 
- Fail: The device could not succesfuly authenticate using 802.1x. Reasons could be:
    - Invalid credentials or configuration
    - Device did not respond to EAP packets
- SKIP: Device did not send any EAP pakcets (likely does not support 802.1x or not configured for 802.1x)