FROM daq/aardvark:latest

RUN $AG update && $AG install python netcat

COPY subset/pentests/user_list.json .
COPY subset/pentests/test_brute .
COPY subset/pentests/brute_client.py .

CMD ./test_brute
