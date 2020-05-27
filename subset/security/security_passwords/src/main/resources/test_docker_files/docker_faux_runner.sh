#!/bin/bash -e

# Runs faux device docker files on all cases pass, fail, skip. Also displays the IP address of the faux container.

# Run example: docker_faux_runner.sh "first_run=true|false"

echo Running docker containers...

if [ "$1" != "true" ]; then
    docker container rm "faux_pass_container"
    docker container rm "faux_fail_container"
    docker container rm "faux_skip_container"
fi

echo ~~~~~~~~~~~~~~~~~~~~~~~ Running faux_pass ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker run --rm -d --name "faux_pass_container" faux_pass
echo Started faux_pass container...
sleep 5
docker exec -it "faux_pass_container" ifconfig
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo ~~~~~~~~~~~~~~~~~~~~~~~ Running faux_fail ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker run --rm -d --name "faux_fail_container" faux_fail
echo Started faux_fail container...
sleep 5
docker exec -it "faux_fail_container" ifconfig
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo ~~~~~~~~~~~~~~~~~~~~~~~ Running faux_skip ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker run --rm -d --name "faux_skip_container" faux_skip
echo Started faux_skip container...
sleep 5
docker exec -it "faux_skip_container" ifconfig
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
echo

echo Done running docker containers...