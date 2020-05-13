# BACnet testing

## test_bacext

The bacext test module includes tests that assess the BACnet stack implementation of BACnet devices.

The tests included in this module are:

- `protocol.bacnet.version`
- `protocol.bacnet.pic`

### Conditions for `protocol.bacnet.version`:

This test retrieves the BACnet protocol version from a BACnet device

- `info` -> BACnet protocol version found from device
- `skip` -> the device under testing is not a BACnet device, test skipped

### Conditions for `protocol.bacnet.pic`:

This test verifies that the device BACnet protocol implementation is compliant to the device PIC statement.

The device PIC statement must be provided in the `aux` folder as a `pics.csv` file.
Check the `src/resources/pics.csv` for an example of this file.

- `pass` -> the BACnet protocol implementation from the device under testing matches the PIC statement
- `fail` -> the BACnet protocol implementation from the device under testing does not match the PIC statement, or a PICS file has been defined but a BACnet device could not be found 
- `skip` -> the test is skipped because the device under testing is not a BACnet device or the PIC statement is not provided 

