#!/bin/bash -e

# Runs the password test on all protocols asynchronously and stores logs in /tmp files.

TARGET_IP_FAUX_1=$1
TARGET_IP_FAUX_2=$2
TARGET_IP_FAUX_3=$3

TARGET_MAC_FAUX_1=$4
TARGET_MAC_FAUX_2=$5
TARGET_MAC_FAUX_3=$6

run_password_test_all_protocols () {
    java -jar security_passwords/build/libs/security_passwords-1.0-SNAPSHOT-all.jar $1 http 80 $2 nginx-site
    java -jar security_passwords/build/libs/security_passwords-1.0-SNAPSHOT-all.jar $1 https 443 $2 nginx-site
    java -jar security_passwords/build/libs/security_passwords-1.0-SNAPSHOT-all.jar $1 telnet 23 $2 nginx-site
    java -jar security_passwords/build/libs/security_passwords-1.0-SNAPSHOT-all.jar $1 ssh 22 $2 nginx-site
}

display_report () {
    cat ./reports/http_result.txt
    cat ./reports/https_result.txt
    cat ./reports/telnet_result.txt
    cat ./reports/ssh_result.txt
}

echo Starting password test run...

echo ~~~~~~~~~~~~~~~~~~~ Running password test on device: $TARGET_IP_FAUX_1 ~~~~~~~~~~~~~~~~~~~~~
run_password_test_all_protocols $TARGET_IP_FAUX_1 $TARGET_MAC_FAUX_1
display_report
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo ~~~~~~~~~~~~~~~~~~~ Running password test on device: $TARGET_IP_FAUX_2 ~~~~~~~~~~~~~~~~~~~~~
run_password_test_all_protocols $TARGET_IP_FAUX_2 $TARGET_MAC_FAUX_2
display_report
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo ~~~~~~~~~~~~~~~~~~~ Running password test on device: $TARGET_IP_FAUX_3 ~~~~~~~~~~~~~~~~~~~~~
run_password_test_all_protocols $TARGET_IP_FAUX_3 $TARGET_MAC_FAUX_3
display_report
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo Done running password tests...

# Keep the container from exiting.
echo Blocking for all eternity.
tail -f /dev/null
