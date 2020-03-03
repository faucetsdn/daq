#!/bin/bash -e

# Runs the password tests on all devices in one go.

# Run example: docker_test_runner.sh "first_run=true|false"

echo Running password test...

if [ "$1" != "true" ]; then
  docker container rm "password_test_container"
fi

echo ~~~~~~~~~~~~~~~~~~~~~~~ Running password test ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker run --name "password_test_container" password_test
echo Started password_test container...
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo
