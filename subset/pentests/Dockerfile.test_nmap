FROM daq/aardvark:latest

RUN $AG update && $AG install nmap netcat jq

COPY subset/pentests/test_nmap .

CMD ./test_nmap
