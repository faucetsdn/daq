# Connection testing

## test_macoui
The MAC OUI test looks up the manufacturer information for the mac address of the device under test.

### Note for test developers 
The functional test code is included in the `mac_oui/src/main/java` folder.

The `macList.txt` file containing the MAC OUI database is downloaded at build time by the container specified in
the `Dockerfile.test_macoui` file.

If java code requires debugging in an IDE, then it will require the `macList.txt` to be placed under the 
`mac_oui/src/main/resources/` folder. Use the curl command from the `Dockerfile.test_macoui` file to download and 
place the file locally into your project. This `.txt` file is git ignored to avoid being included as a 
static resource on the source code repo.

### Conditions for mac_oui
 - pass -> if the MAC OUI matches the mac prefix IEEE registration.
 - fail -> if the MAC OUI does not match with any of the mac prefixes.

