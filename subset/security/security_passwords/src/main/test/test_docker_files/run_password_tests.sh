#!/bin/bash -e

# Runs the password test on all protocols, for each of the faux devices.

TARGET_IP_FAUX_1=$1
TARGET_IP_FAUX_2=$2
TARGET_IP_FAUX_3=$3
TARGET_MAC=$4

run_password_test_all_protocols () {
  echo Running on http
  java -jar security_passwords/build/libs/security_passwords-1.0-SNAPSHOT-all.jar $1 http 80 $TARGET_MAC nginx-site

  echo Running on https
  java -jar security_passwords/build/libs/security_passwords-1.0-SNAPSHOT-all.jar $1 https 443 $TARGET_MAC nginx-site

  echo Running on telnet
  java -jar security_passwords/build/libs/security_passwords-1.0-SNAPSHOT-all.jar $1 telnet 23 $TARGET_MAC nginx-site

  echo Running on ssh
  java -jar security_passwords/build/libs/security_passwords-1.0-SNAPSHOT-all.jar $1 ssh 22 $TARGET_MAC nginx-site
}

display_report () {
  cat ./reports/http_report.txt
  cat ./reports/https_report.txt
  cat ./reports/telnet_report.txt
  cat ./reports/ssh_report.txt
}

echo Starting password test run...

echo ~~~~~~~~~~~~~~~~~~~ Running password test on device: $TARGET_IP_FAUX_1 ~~~~~~~~~~~~~~~~~~~~~
run_password_test_all_protocols $TARGET_IP_FAUX_1
display_report
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo ~~~~~~~~~~~~~~~~~~~ Running password test on device: $TARGET_IP_FAUX_2 ~~~~~~~~~~~~~~~~~~~~~
run_password_test_all_protocols $TARGET_IP_FAUX_2
display_report
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo ~~~~~~~~~~~~~~~~~~~ Running password test on device: $TARGET_IP_FAUX_3 ~~~~~~~~~~~~~~~~~~~~~
run_password_test_all_protocols $TARGET_IP_FAUX_3
display_report
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo Done running password tests...
