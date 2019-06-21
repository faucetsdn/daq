# Image name: daq/faux
#
# Faux device for framework development/testing.
#

FROM daq/aardvark:latest as bacnet_build

# Run this separately so it can be shared with other builds.
RUN $AG update && $AG install openjdk-8-jre

RUN $AG update && $AG install openjdk-8-jdk git

ENV BACHASH=6abd3cfcfe6cfb95f444638515a0b21f547a1202

RUN bin/retry_cmd git clone https://github.com/grafnu/bacnet4j.git --single-branch \
  && cd bacnet4j && git reset --hard $BACHASH && ../bin/retry_cmd ./gradlew shadow

FROM daq/aardvark:latest

# Run this separately so it can be shared with other builds.
RUN $AG update && $AG install openjdk-8-jre

RUN $AG update && $AG install isc-dhcp-client ethtool network-manager netcat curl\
    python ifupdown openssl ssh

# Prefetch resolvconf to dynamically install at runtime in start_faux.
RUN $AG update && cd /tmp && ln -s ~/bin bin && $AG download resolvconf && mv resolvconf_*.deb ~

COPY --from=bacnet_build /root/bacnet4j/*.jar bacnet4j/

COPY subset/pentests/brute_server.py pentests/
COPY subset/security/tlsfaux tlsfaux/
COPY misc/start_faux bin/
COPY misc/bacnet_discover bin/

# Weird workaround for problem running tcdump in a privlidged container.
RUN mv /usr/sbin/tcpdump /usr/bin/tcpdump

ENTRYPOINT ["bin/start_faux"]
