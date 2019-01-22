# Image name: daq/networking
#
# Image used for testing a mock OpenFlow switch.
#

FROM daq/aardvark:latest

RUN $AG update && $AG install netcat python

COPY misc/test_hold .

CMD ./test_hold
