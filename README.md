# DAQ: <b>D</b>evice <b>A</b>utomated <b>Q</b>ualification for IoT Devices.

Flexble IoT device qualification framework utilizing the FAUCET SDN controller.

## Build instructions

### Prerequisites

Tested with ```Linux 4.9.0-5-amd64 #1 SMP Debian 4.9.65-3+deb9u2 (2018-01-04) x86_64 GNU/Linux```, YMMV.

* Install [Open vSwitch Debian Install](http://docs.openvswitch.org/en/latest/intro/install/distributions/#debian)
  (tested with version 2.6.2).
* Install [Docker CE Debian Install](https://docs.docker.com/install/linux/docker-ce/debian/)
  (tested with version 17.12.0-ce).
* Also need to add user to docker group (as described on install docker page).

### Building DAQ

See <code>docker/Dockerfile.runner</code> for all your basic building needs:

<pre>
  docker build -t daq/runner -f docker/Dockerfile.runner .
</pre>

Now you can drop into a daq-compliant shell:

<pre>
  ~/daq$ docker run -ti daq/runner
  root@XXXXXXXXX:~# ls
  daq  faucet
</pre>

(You can also run everything natively if you're on a suitably compatible system and the
appropriate dependencies are installed.)

