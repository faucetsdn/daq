# Connection testing

## test_macoui
The MAC OUI test looks up the manufacturer information for the mac address of the device under test.

This test has a `must pass` test policy.
 
Test are included in the module mac_oui - `Main.java`. The macList.txt is downloaded at build time 
by the Dockerfile.test_macoui. If java code needs to be debugged in an IDE then it will require the 
macList.txt to be placed under the /src/main/resources/ folder. Use the curl command from the 
Dockerfile.test_macoui to download and place the file locally into your project. This txt file is 
git ignored. So make sure you DO NOT to push the static resource on to the repo again.

### Conditions for mac_oui
 - pass -> if the MAC OUI matches the mac prefix IEEE registration.
 - fail -> if the MAC OUI does not match with any of the mac prefixes.

