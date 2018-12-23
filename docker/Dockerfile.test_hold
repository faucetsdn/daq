FROM daq/aardvark:latest

RUN $AG update && $AG install ethtool netcat curl nmap

COPY misc/test_hold .

CMD ./test_hold
