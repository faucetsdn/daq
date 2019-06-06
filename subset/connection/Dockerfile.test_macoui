FROM daq/aardvark:latest 

RUN $AG update && $AG install openjdk-8-jre

RUN $AG update && $AG install openjdk-8-jdk git

COPY subset/connection/ .

RUN cd mac_oui && ./gradlew shadowJar 

CMD ["./test_macoui"]
