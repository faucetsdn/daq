#!/bin/bash -e

# Builds all the docker files. Make sure this is run from the DAQ root directory.

echo Building docker files...

echo ~~~~~~~~~~~~~~~~~~~~~~~ Building faux_pass ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker build -f subset/security/security_passwords/src/main/test/test_docker_files/Dockerfile.faux_pass -t "faux_pass" .
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo ~~~~~~~~~~~~~~~~~~~~~~~ Building faux_fail ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker build -f subset/security/security_passwords/src/main/test/test_docker_files/Dockerfile.faux_fail -t "faux_fail" .
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo ~~~~~~~~~~~~~~~~~~~~~~~ Building faux_skip ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker build -f subset/security/security_passwords/src/main/test/test_docker_files/Dockerfile.faux_skip -t "faux_skip" .
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo ~~~~~~~~~~~~~~~~~~~~~~~ Building password_test ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker build -f subset/security/security_passwords/src/main/test/test_docker_files/Dockerfile.password_test -t "password_test" .
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo Built all docker files...
