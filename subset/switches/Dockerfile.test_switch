FROM daq/aardvark:latest

# Do this alone first so it can be re-used by other build files.
RUN $AG update && $AG install openjdk-8-jre

RUN $AG update && $AG install openjdk-8-jdk git

RUN $AG update && $AG install maven tcpdump

COPY subset/switches/ switches/ 

RUN cd switches && mvn clean compile assembly:single

CMD ["./switches/test_switch"]
