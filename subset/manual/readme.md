# Manual Tests


## Manual Tests
Some tests cannot be automated with DAQ although these may be required. To facilitate a single test report which incorporates all tests undertaken on a device, the `manual` test can be used to input the results into reports produced by DAQ. 

## Configuration
Manual tests including results are inserted into the device's `module_config.json` and marked by `"type": "manual"`.

```
"tests": {
    "manual.test.name": {
        "description": "test description",
        "enabled": true,
        "type": "manual",
        "result": "required",   
        "outcome": "pass"   
        "summary" : "summary note in results table",
        "test_log" : "additional information in report appendix"
    }
}
```


## Example Report of Manual Tests
In summary table
|Result|Test|Category|Expectation|Notes|
|---|---|---|---|---|
|pass|manual.test.name|Security|Recommended|Manual test|

In report appendix
```
--------------------
manual.test.name
--------------------
Test description
--------------------
Test description
--------------------
RESULT pass manual.test.name Manual test - Test summary
```