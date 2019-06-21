## Image name: daq/gauge

FROM faucet/python3

COPY faucet/ /faucet-src/

RUN /faucet-src/docker/install-faucet.sh && rm -rf /faucet-src/.git

# Check for target executable since installer doesn't error out properly.
RUN which faucet

RUN apk add -q tcpdump iptables

CMD ["gauge"]
