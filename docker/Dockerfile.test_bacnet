FROM daq/aardvark:latest as bacnet_build

# Do this alone first so it can be re-used by other build files.
RUN $AG update && $AG install openjdk-8-jre

RUN $AG update && $AG install openjdk-8-jdk git

ENV BACHASH=6abd3cfcfe6cfb95f444638515a0b21f547a1202

RUN bin/retry_cmd git clone https://github.com/grafnu/bacnet4j.git --single-branch \
  && cd bacnet4j && git reset --hard $BACHASH && ../bin/retry_cmd ./gradlew shadow

FROM daq/aardvark:latest

RUN $AG update && $AG install openjdk-8-jre

COPY --from=bacnet_build /root/bacnet4j/*.jar bacnet4j/

COPY misc/bacnet_discover .

CMD ["./bacnet_discover"]
