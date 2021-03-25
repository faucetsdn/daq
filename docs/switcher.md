# Control Plane Switch Access

This setup defines how to access the the control plane from a container test.

## Required Config
* Configurations of the the access switch can be specified under swith_setup of the system config. An example of switch_setup is available under <b>config/system/ext.yaml</b>. Descriptions of these config options are available under <b>proto/system_config.proto</b>.

* In addition to the `lo_addr` and `ip_addr` config values, setting
`mods_addr` will enable switch control-plane access. It should be set
to a pattern for the test container IP, e.g. `192.0.3.%d/24`, where
the `%d` will be automaticaly replaced with test port set number.
Doing this causes the `LOCAL_IP` and `SWITCH_IP` env variables to be set in test containers. See `subset/ping/test_ping` for an example of how to use them.

* If `ctrl_intf` is defined, then this will enable utilization of the actual physical
switch. If `ctrl_intf` is _not_ defined, then the system will spin up a special `daq-switch` Docker container, defined by `Dockerfile.switch`, to masquerade as the switch for unit testing.

## Test Run
This is a sample test run while using a simulated docker switch container
along with an 'external' OVS switch as per the automated integration tests.
<pre>
~/daq$ <b>echo "include: ../config/system/ext.yaml" > local/system.yaml</b>
~/daq$ <b>cmd/run -s</b>
Flattening config from local/system.yaml into inst/config/system.conf
Running switch setup...
Using default cplane_mac f8:39:71:c9:7a:09
Cleaning old setup...
Creating ovs-link interfaces...
Creating local-link interfaces...
Creating local bridge ctrl-br...
Configuring ctrl-swy with 192.0.2.10/24
Creating daq-switch as per FAUX_SWITCH switch model.
daq-switch
Creating daq-switch at 192.0.2.138/24 linked via ctrl-swa
DAQ autoclean docker rm -f daq-switch
DAQ autoclean ip link del ctrl-swa
Ignoring interface ext-ovs-ctl in favor of ctrl-swa
Skipping bring-up of ovs switch interface ext-ovs-pri
Bridging ctrl-swa to ctrl-br
Warmup ping for 192.0.2.138
PING 192.0.2.138 (192.0.2.138) 56(84) bytes of data.
64 bytes from 192.0.2.138: icmp_seq=1 ttl=64 time=16.9 ms
64 bytes from 192.0.2.138: icmp_seq=2 ttl=64 time=0.052 ms

--- 192.0.2.138 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1027ms
rtt min/avg/max/mdev = 0.061/0.188/0.315/0.127 ms
Done with local switch setup.
&hellip;
INFO:mininet:*** Starting 1 switches
INFO:mininet:pri
INFO:mininet:...
<b>INFO:network:Attaching switch interface ctrl-pri on port 1000</b>
INFO:runner:Waiting for system to settle...
INFO:runner:Entering main event loop.
INFO:runner: See docs/troubleshooting.md if this blocks for more than a few minutes.
INFO:runner:Port 2 dpid 4886718345 is now active True
&hellip;
INFO:runner:Done with runner.
INFO:daq:DAQ runner returned 0
Cleanup ovs-vsctl del-br ext-ovs
Cleanup ip link del ext-ovs-pri
Cleanup docker rm -f daq-switch
daq-switch
Cleanup ip link del ctrl-swa
Cannot find device "ctrl-swa"
Cleanup ip link del ctrl-pri
Cleanup ip link del ctrl-swx
Cleanup ovs-vsctl --if-exists del-br ctrl-br
Cleanup docker cp daq-usi:/root/logs.txt inst/cmdusi.log
Cleanup docker kill daq-usi
daq-usi
Cleanup docker kill daq-faux
daq-faux
Done with run, exit 0
~/daq$ <b>cat inst/run-9a02571e8f02/nodes/ping02/activate.log</b>

Baseline ping test report
&hellip;
reading from file /home/username/daq/inst/run-9a02571e8f02/test_root/scans/startup.pcap, link-type EN10MB (Ethernet)
%% 40 packets captured.
&hellip;
<b>Configuring network with local address 192.0.2.122/24</b>
Using IP index 122
PING 192.0.2.138 (192.0.2.138) 56(84) bytes of data.
64 bytes from 192.0.2.138: icmp_seq=1 ttl=64 time=0.026 ms
64 bytes from 192.0.2.138: icmp_seq=2 ttl=64 time=0.024 ms

--- 192.0.2.138 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 27ms
rtt min/avg/max/mdev = 0.024/0.025/0.026/0.001 ms
&hellip;
Critical module status is pass
</pre>
