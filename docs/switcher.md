# Control Plane Switch Access

This setup defines how to access the the control plane from a container test.

## Required Config
In addition to the `ext_ofip` and `ext_addr` config values, setting
`ext_loip` will enable switch control-plane access. It should be set
to a pattern for the test container IP, e.g. `192.0.3.@/16`, where
the `@` will be automaticaly replaced with test port set number.
Doing this causes the `LOCAL_IP` and `SWITCH_IP` env variables to be set in
test containers. See `misc/test_ping` for an example of how to use them.

If `ext_ctrl` is defined, then this will enable access to the actual physical
switch. If `ext_ctrl` is _not_ defined, then the system will spin up a special
`daq-switch` Docker container, defined by `Dockerfile.switch`, to masquerade as
the switch for unit testing.

## Test Run
This is a sample test run while using a simulated docker switch container
along with an 'external' OVS switch as per the automated integration tests.
<pre>
~/daq$ <b>cp misc/system_ext.conf local/system.conf</b>
~/daq$ <b>cmd/run -s</b>
Loading config from local/system.conf
Starting Sun Dec 23 08:36:09 PST 2018, run_mode is local
Clearing previous reports...
Running as root...
Loading config from local/system.conf
Release version 0.9.0
cleanup='echo cleanup'
ext_addr=192.0.2.138
ext_dpid=0x123456789
ext_intf=ext-ovs-pri
<b>ext_loip=192.0.3.@/16</b>
ext_ofip=192.0.2.10/16
ext_ofpt=6666
run_mode=local
sec_port=7
&hellip;
Loading config from local/system.conf
Using default cplane_mac f8:39:71:c9:7a:09
Cleaning old setup...
Creating ovs-link interfaces...
Creating local-link interfaces...
Creating local bridge...
Creating daq-switch, because only ext_addr defined.
daq-switch
<b>Creating docker with veth -swb at 192.0.2.138/16</b>
Bridging ctrl-swa to ctrl-br
<b>Configuring ctrl-swy with 192.0.2.10/16</b>
Checking external connection to 192.0.2.138
PING 192.0.2.138 (192.0.2.138) 56(84) bytes of data.
64 bytes from 192.0.2.138: icmp_seq=1 ttl=64 time=0.315 ms
64 bytes from 192.0.2.138: icmp_seq=2 ttl=64 time=0.061 ms

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
INFO:runner:If this blocks for too long, check inst/faucet.log for errors
INFO:runner:Port 2 dpid 4886718345 is now active True
INFO:runner:System port 7 on dpid 4886718345 is active True
&hellip;
INFO:runner:Done with runner.
INFO:daq:DAQ runner returned 0
Cleanup ovs-vsctl del-br ext-ovs
Cleanup ip link del ext-ovs-pri
Cleanup docker kill daq-faux
daq-faux
Done with run, exit 0
~/daq$ <b>cat inst/run-port-02/nodes/ping02/activate.log</b>

-rw-r--r-- 1 root root 8674 Dec 23 16:37 /scans/startup.pcap
reading from file /scans/startup.pcap, link-type EN10MB (Ethernet)
66 packets captured.
&hellip;
<b>Configuring network with local address 192.0.3.22/16</b>
PING 192.0.2.138 (192.0.2.138) 56(84) bytes of data.
64 bytes from 192.0.2.138: icmp_seq=1 ttl=64 time=2056 ms
64 bytes from 192.0.2.138: icmp_seq=2 ttl=64 time=1025 ms
64 bytes from 192.0.2.138: icmp_seq=3 ttl=64 time=1.52 ms
64 bytes from 192.0.2.138: icmp_seq=4 ttl=64 time=0.136 ms
64 bytes from 192.0.2.138: icmp_seq=5 ttl=64 time=0.127 ms

--- 192.0.2.138 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4070ms
&hellip;
Passed basic connectivity tests.
</pre>
