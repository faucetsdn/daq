#!/bin/bash
set -o pipefail

source etc/FILES_MAPPING

mkdir -p out
test_script=${0##*/}
def_name=${test_script%.sh}.out
TEST_RESULTS=${TEST_RESULTS:-out/$def_name}
GOLDEN_FILE=testing/$def_name

echo Shunt Test > $TEST_RESULTS

docker-compose -f ./testing/shunt/docker-compose.yaml up --build -d
sleep 6
docker exec shunt_host_client_1 ps ax
docker exec shunt_host_client_1 ping -c 1 192.168.1.1

if [ $? -eq 0 ]; then
    echo Ping succesful | tee -a $TEST_RESULTS
else
    echo Ping unsuccesful | tee -a $TEST_RESULTS
fi

docker exec shunt_host_server_1 bash -c "source bin/shunt_functions; clean_vxlan_ssh_conn"

sleep 10
docker logs shunt_host_server_1


docker exec shunt_host_server_1 ps ax
docker exec shunt_host_client_1 ping -c 1 192.168.1.1

if [ $? -eq 0 ]; then
    echo Ping succesful | tee -a $TEST_RESULTS
else
    echo Ping unsuccesful | tee -a $TEST_RESULTS
fi

docker-compose -f ./testing/shunt/docker-compose.yaml down

echo Done with tests | tee -a $TEST_RESULTS

exit_code=0
echo
echo Test results $TEST_RESULTS
cat $TEST_RESULTS
echo
echo Comparing $GOLDEN_FILE against $TEST_RESULTS
diff $GOLDEN_FILE $TEST_RESULTS | cat -vet || exit_code=1
echo

echo Done with tests.
exit $exit_code
