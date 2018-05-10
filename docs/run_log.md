<pre>
<b>~/daq$ cmd/run -s</b>
Loading container configuration from /home/hamilton/daq/local/system.conf
0.5.8: Pulling from daqf/runner
Digest: sha256:8848a04c26c612901fca40ce356ca4bf6c548604ac72423b81d819a75cc49663
Status: Image is up to date for daqf/runner:0.5.8
Configuring apparmor...
apparmor_parser: Unable to remove "/usr/sbin/tcpdump".  Profile doesn't exist
Starting daqf/runner:0.5.8 -s...
Loading daq run configuration from /root/daq/local/system.conf
daq_intf='faux!'
ext_intf=enx00e04c680253
ext_port=7
site_description='Default Configuration'
 * Starting Docker: docker
   ...done.
ovsdb-server is not running
ovs-vswitchd is not running
 * /etc/openvswitch/conf.db does not exist
 * Creating empty database /etc/openvswitch/conf.db
 * Starting ovsdb-server
 * system ID not configured, please use --system-id
 * Configuring Open vSwitch system IDs
 * Starting ovs-vswitchd
 * Enabling remote OVSDB managers
Implicitly running faux device...
Launching faux ...
intf faux!
Removing old interface faux
Adding new interface to 291...
Done with faux device launch.
3: faux@if2: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state LOWERLAYERDOWN group default qlen 1000
    link/ether 8e:0b:3f:9e:48:86 brd ff:ff:ff:ff:ff:ff link-netnsid 1
Executing runner -s...
INFO:gcp:No gcp_cred credential specified in config
WARNING:mininet:*** Error setting resource limits. Mininet's performance may be affected.
INFO:daq:Starting faucet...
INFO:daq:Creating ovs secondary with dpid/port 2/7
INFO:daq:Added switch link pri-eth1 <-> sec-eth7
INFO:daq:Starting mininet...
INFO:mininet:*** Configuring hosts
INFO:mininet:*** Starting controller
INFO:mininet:controller
INFO:mininet:*** Starting 2 switches
INFO:mininet:pri
INFO:mininet:sec
INFO:mininet:...
INFO:daq:Attaching device interface faux on port 1.
INFO:daq:Waiting for system to settle...
INFO:daq:Entering main event loop.
INFO:daq:Set 1 created.
INFO:daq:Set 1 activating.
INFO:daq:Set 1 ping test gw01->dummy01
INFO:daq:Set 1 ping test dummy01->gw01
INFO:daq:Set 1 ping test dummy01->192.168.84.38
INFO:daq:Set 1 ping test gw01->dummy01 from 192.168.84.38
INFO:daq:Set 1 waiting for dhcp reply from gw01...
INFO:daq:Set 1 received dhcp reply: 6e:25:c7:3b:1a:ec is at 10.20.183.108
INFO:daq:Set 1 background scan for 20 seconds...
INFO:daq:Set 1 monitor scan complete
INFO:daq:Set 1 ping test gw01->10.20.183.108
INFO:daq:Set 1 ping test gw01->10.20.183.108 from 192.168.84.38
INFO:daq:Set 1 running docker test pass
INFO:daq:Set 1 PASSED test pass
INFO:daq:Set 1 running docker test fail
INFO:daq:Set 1 FAILED test fail with error 1: None
INFO:daq:Set 1 running docker test ping
INFO:daq:Set 1 PASSED test ping
INFO:daq:Set 1 running docker test bacnet
INFO:daq:Set 1 PASSED test bacnet
INFO:daq:Set 1 running docker test nmap
INFO:daq:Set 1 PASSED test nmap
INFO:daq:Set 1 running docker test mudgee
INFO:daq:Set 1 PASSED test mudgee
INFO:daq:Set 1 terminate, trigger True
INFO:daq:Set 1 terminate, trigger False
INFO:daq:Set 1 cancelled.
INFO:daq:Set 1 complete, 12 results
INFO:daq:Remaining sets: []
INFO:mininet:*** Stopping 1 controllers
INFO:mininet:controller
INFO:mininet:*** Stopping 1 links
INFO:mininet:.
INFO:mininet:*** Stopping 2 switches
INFO:mininet:pri
INFO:mininet:sec
INFO:mininet:*** Stopping 1 hosts
INFO:mininet:gw01
INFO:mininet:*** Done
INFO:daq:Done with runner.
0 file_references
Killing daq-faux container...
Done with run.
<b>~/daq$ </b>
</pre>
