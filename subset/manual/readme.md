# Manual Tests

## Todo
- add to travis ci test for whichever device is the one for the report




## Manual Tests
Some tests cannot be automated with DAQ and  The `manual` test inserts 

## Configuration
Manual tests are inserted into the device's `module_config.json` and marked by `"type": "manual"`.

```
"tests": {
    "connection.wireless_ap_disabled": {
        "description": "Verify that the devices is configured not to act as an access point and not to have any hidden SSID",
        "enabled": true,
        "type": "manual",
        "result": "required",
        "outcome": "pass",
        "summary" : 
        "
    }
}
```

The following key-value pairs are permitted for manual tests:

| Option | Description |
| --- | --- |
| Outcome | Did the manual test _pass_,_fail_ or  |
| Outcome | pass, fail, info |


## Example Report of Manual Tests
Test output added i