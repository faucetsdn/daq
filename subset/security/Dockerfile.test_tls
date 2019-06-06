FROM daq/aardvark:latest

# Do this alone first so it can be re-used by other build files.
RUN $AG update && $AG install openjdk-8-jre

RUN $AG update && $AG install openjdk-8-jdk git

COPY subset/security/ . 

RUN cd tlstest && ./gradlew build

CMD ["./test_tls"]
