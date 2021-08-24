<pre>
username@hostname:~/daq$ <b>mkdir -p local</b>
username@hostname:~/daq$ <b>echo "include: ../config/system/all.conf" > local/system.yaml</b>
username@hostname:~/daq$ <b>echo "host_tests: config/modules/host.conf" >> local/system.yaml</b>
username@hostname:~/daq$ <b>cmd/run -s</b>
Activating venv
Flattening config from local/system.yaml into inst/config/system.conf
Starting Wed MM dd hh:mm:ss UTC 2021
Clearing previous state...
Running as root...
Activating venv
Flattening config from local/system.yaml into inst/config/system.conf
HEAD is now at 778ed989 Merge pull request #3726 from gizmoguy/test-base-8.0.6
HEAD is now at 72996a10 fix device report server logic (#289)
Release version
ovsdb-server is running with pid 13512
ovs-vswitchd is running with pid 13558
No external switch model specified.
daq-usi
DAQ autostart gcp_cred= cmd/usi
Starting USI in debug mode
ed4c4c5750cdb402a3ebbb13212a5bbface8f26027c20144f699aef471e0bdb8
DAQ autoclean docker cp daq-usi:/root/logs.txt inst/cmdusi.log
DAQ autoclean docker kill daq-usi
Activating venv
Flattening config from local/system.yaml into inst/config/system.conf
Autostarting system components...
DAQ autostart cmd/faux 1
Activating venv
Flattening config from local/system.yaml into inst/config/system.conf
Launching faux ...
Clensing old container daq-faux-1
DAQ autoclean docker kill daq-faux-1
Removing old interface faux-1
Adding new interface to 17828...
Done with faux device launch.
DAQ autostart cmd/faux 2
Activating venv
Flattening config from local/system.yaml into inst/config/system.conf
Launching faux ...
Clensing old container daq-faux-2
DAQ autoclean docker kill daq-faux-2
Removing old interface faux-2
Adding new interface to 18089...
Done with faux device launch.
DAQ autostart cmd/faux 3
Activating venv
Flattening config from local/system.yaml into inst/config/system.conf
Launching faux ...
Clensing old container daq-faux-3
DAQ autoclean docker kill daq-faux-3
Removing old interface faux-3
Adding new interface to 18341...
Done with faux device launch.
Activating venv
Flattening config from local/system.yaml into inst/config/system.conf
No LSB modules are available.
Entering virtual python environment...
Using python3 at /home/username/daq/venv/bin/python3
Prepending /home/username/daq/binhack to PATH
Executing: python3 daq/daq.py local/system.yaml -s usi_setup.url=172.17.0.1:5000
processing arg: local/system.yaml
Including config file /home/username/daq/local/../config/system/all.conf
Including config file /home/username/daq/config/system/default.yaml
processing arg: -s
processing arg: usi_setup.url=172.17.0.1:5000
base_conf=/home/username/daq/resources/setups/baseline/base_config.json
default_timeout_sec=350
dhcp_lease_time=500s
finish_hook=/home/username/daq/bin/dump_network
host_tests=config/modules/host.conf
initial_dhcp_lease_time=120s
interfaces.faux-1.opts=
interfaces.faux-2.opts=
interfaces.faux-3.opts=
internal_subnet.subnet=10.20.0.0/16
long_dhcp_response_sec=105
monitor_scan_sec=30
port_flap_timeout_sec=5
settle_sec=5
single_shot=True
site_description="Multi-Device All-Tests Configuration"
site_path=local/site/
switch_setup.of_dpid=2
switch_setup.uplink_port=4
topology_hook=/home/username/daq/bin/dump_network
usi_setup.rpc_timeout_sec=20
usi_setup.url=172.17.0.1:5000
MM dd hh:mm:ss daq      INFO    pid is 18515
MM dd hh:mm:ss gcp      INFO    No gcp_cred file specified in config, disabling gcp use.
MM dd hh:mm:ss runner   INFO    Loading base config from /home/username/daq/resources/setups/baseline/base_config.json
MM dd hh:mm:ss config   INFO    Including config file /home/username/daq/resources/setups/baseline/../common/base_config.json
MM dd hh:mm:ss runner   INFO    Loading site config from local/site/site_config.json
MM dd hh:mm:ss config   INFO    Skipping missing config file local/site/site_config.json
MM dd hh:mm:ss topology INFO    No device_specs file specified, skipping...
MM dd hh:mm:ss runner   INFO    Reading test definition file config/modules/host.conf
MM dd hh:mm:ss runner   INFO    Reading test definition file /home/username/daq/subset/pentests/build.conf
MM dd hh:mm:ss runner   INFO    Reading test definition file /home/username/daq/usi/build.conf
MM dd hh:mm:ss runner   INFO    Reading test definition file /home/username/daq/subset/ipaddr/build.conf
MM dd hh:mm:ss runner   INFO    DAQ RUN id: 88e076a1-fab4-4a38-84e9-8e32990fada5
MM dd hh:mm:ss runner   INFO    Configured with tests pass, fail, ping, bacnet, mudgee, nmap, discover, ipaddr
MM dd hh:mm:ss runner   INFO    DAQ version 1.10.2-30-g0705b486-dirty
MM dd hh:mm:ss runner   INFO    LSB release Distributor ID: Debian Description: Debian GNU/Linux 10 (buster) Release: 10 Codename: buster
MM dd hh:mm:ss runner   INFO    system uname Linux instance-1 4.19.0-13-cloud-amd64 #1 SMP Debian 4.19.160-2 (2020-11-28) x86_64 GNU/Linux
MM dd hh:mm:ss network  INFO    Activating faucet topology...
MM dd hh:mm:ss topology INFO    Starting faucet...
MM dd hh:mm:ss topology INFO    Starting gauge...
MM dd hh:mm:ss network  INFO    Initializing faucitizer...
MM dd hh:mm:ss faucetizer INFO    Reading structural config file: inst/faucet_intermediate.yaml
MM dd hh:mm:ss network  INFO    Waiting 5s for network to settle
MM dd hh:mm:ss network  INFO    Creating ovs sec with dpid/port 2/4
MM dd hh:mm:ss network  INFO    Added switch link pri-eth1 <-> sec-eth4
MM dd hh:mm:ss network  INFO    Attaching device interface faux-1 on port 1.
MM dd hh:mm:ss network  INFO    Attaching device interface faux-2 on port 2.
MM dd hh:mm:ss network  INFO    Attaching device interface faux-3 on port 3.
MM dd hh:mm:ss network  INFO    Starting mininet...
MM dd hh:mm:ss mininet  INFO    *** Configuring hosts
MM dd hh:mm:ss mininet  INFO    *** Starting controller
MM dd hh:mm:ss mininet  INFO    faucet
MM dd hh:mm:ss mininet  INFO    gauge
MM dd hh:mm:ss mininet  INFO    *** Starting 2 switches
MM dd hh:mm:ss mininet  INFO    pri
MM dd hh:mm:ss mininet  INFO    sec
MM dd hh:mm:ss mininet  INFO    ...
MM dd hh:mm:ss fevent   INFO    Connecting to socket path /home/username/daq/inst/faucet_event.sock
MM dd hh:mm:ss runner   INFO    Waiting for system to settle...
MM dd hh:mm:ss runner   INFO    Entering main event loop.
MM dd hh:mm:ss runner   INFO    See docs/troubleshooting.md if this blocks for more than a few minutes.
MM dd hh:mm:ss runner   INFO    System port 1 on dpid 1 is active True
MM dd hh:mm:ss runner   INFO    Port 3 dpid 2 is now active
MM dd hh:mm:ss runner   INFO    Port 2 dpid 2 is now active
MM dd hh:mm:ss runner   INFO    Port 1 dpid 2 is now active
MM dd hh:mm:ss runner   INFO    Port 3 dpid 2 learned 9a:02:57:1e:8f:03
MM dd hh:mm:ss runner   INFO    Gateway for device group 9a02571e8f03 not found, initializing base 3...
MM dd hh:mm:ss gateway  INFO    Initializing gateway 9a02571e8f03 as gw03/30
MM dd hh:mm:ss gateway  INFO    Added networking host gw03 on port 30 at 10.20.0.1
MM dd hh:mm:ss gateway  INFO    Added fake target fake03 on port 31 at 10.20.0.2
MM dd hh:mm:ss runner   INFO    Test ping gw03->fake03
MM dd hh:mm:ss runner   INFO    Test ping gw03->fake03
MM dd hh:mm:ss runner   INFO    Test ping fake03->gw03
MM dd hh:mm:ss runner   INFO    Test ping fake03->192.168.84.3
MM dd hh:mm:ss runner   INFO    Test ping gw03->fake03 from 192.168.84.3
MM dd hh:mm:ss gateway  INFO    Gateway 3 change lease time to 120s
MM dd hh:mm:ss gateway  INFO    Gateway 3 startup capture gw03-eth0 in container's /tmp/gateway.pcap
MM dd hh:mm:ss dhcp     INFO    DHCP monitor gw03 waiting for replies...
MM dd hh:mm:ss gateway  INFO    Attaching target 9a02571e8f03 to gateway group 9a02571e8f03
MM dd hh:mm:ss host     INFO    Loading device module config from /home/username/daq/local/site/mac_addrs/9a02571e8f03/device_config.json
MM dd hh:mm:ss host     INFO    Device config reloaded: True 9a02571e8f03 on port 3
MM dd hh:mm:ss config   INFO    Writing config to /home/username/daq/local/site/mac_addrs/9a02571e8f03/aux/module_config.json
MM dd hh:mm:ss host     INFO    Host 9a:02:57:1e:8f:03 running with enabled tests ['pass', 'fail', 'ping', 'bacnet', 'mudgee', 'nmap', 'discover']
MM dd hh:mm:ss report   INFO    Writing report to inst/reports/report_9a02571e8f03_2021-03-24T212315.*
MM dd hh:mm:ss report   INFO    Writing alternate report to local/site/mac_addrs/9a02571e8f03/report.*
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 initializing...
MM dd hh:mm:ss host     INFO    Loading base module config from /home/username/daq/local/site/mac_addrs/9a02571e8f03/base_config.json
MM dd hh:mm:ss network  INFO    Creating mirror pair mirror-3 <-> mirror-3-ext at 1003
MM dd hh:mm:ss host     INFO    Executing topology_hook: /home/username/daq/bin/dump_network inst/network
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 startup pcap capture
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 pcap intf mirror-3 for infinite seconds output in run-9a02571e8f03/scans/startup.pcap
MM dd hh:mm:ss network  INFO    Directing traffic for 9a:02:57:1e:8f:03 on port 3 to 3
MM dd hh:mm:ss faucetizer INFO    Reading structural config file: inst/faucet_intermediate.yaml
MM dd hh:mm:ss network  INFO    Waiting 5s for network to settle
MM dd hh:mm:ss runner   INFO    Port 2 dpid 2 learned 9a:02:57:1e:8f:02
MM dd hh:mm:ss runner   INFO    Gateway for device group 9a02571e8f02 not found, initializing base 2...
MM dd hh:mm:ss gateway  INFO    Initializing gateway 9a02571e8f02 as gw02/20
MM dd hh:mm:ss gateway  INFO    Added networking host gw02 on port 20 at 10.20.0.3
MM dd hh:mm:ss gateway  INFO    Added fake target fake02 on port 21 at 10.20.0.4
MM dd hh:mm:ss runner   INFO    Test ping gw02->fake02
MM dd hh:mm:ss runner   INFO    Test ping gw02->fake02
MM dd hh:mm:ss runner   INFO    Test ping fake02->gw02
MM dd hh:mm:ss runner   INFO    Test ping fake02->192.168.84.2
MM dd hh:mm:ss runner   INFO    Test ping gw02->fake02 from 192.168.84.2
MM dd hh:mm:ss gateway  INFO    Gateway 2 change lease time to 120s
MM dd hh:mm:ss gateway  INFO    Gateway 2 startup capture gw02-eth0 in container's /tmp/gateway.pcap
MM dd hh:mm:ss dhcp     INFO    DHCP monitor gw02 waiting for replies...
MM dd hh:mm:ss gateway  INFO    Attaching target 9a02571e8f02 to gateway group 9a02571e8f02
MM dd hh:mm:ss host     INFO    Loading device module config from /home/username/daq/local/site/mac_addrs/9a02571e8f02/device_config.json
MM dd hh:mm:ss host     INFO    Device config reloaded: True 9a02571e8f02 on port 2
MM dd hh:mm:ss config   INFO    Writing config to /home/username/daq/local/site/mac_addrs/9a02571e8f02/aux/module_config.json
MM dd hh:mm:ss host     INFO    Host 9a:02:57:1e:8f:02 running with enabled tests ['pass', 'fail', 'ping', 'bacnet', 'mudgee', 'nmap', 'discover']
MM dd hh:mm:ss report   INFO    Writing report to inst/reports/report_9a02571e8f02_2021-03-24T212329.*
MM dd hh:mm:ss report   INFO    Writing alternate report to local/site/mac_addrs/9a02571e8f02/report.*
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 initializing...
MM dd hh:mm:ss host     INFO    Loading base module config from /home/username/daq/local/site/mac_addrs/9a02571e8f02/base_config.json
MM dd hh:mm:ss network  INFO    Creating mirror pair mirror-2 <-> mirror-2-ext at 1002
MM dd hh:mm:ss host     INFO    Executing topology_hook: /home/username/daq/bin/dump_network inst/network
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 startup pcap capture
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 pcap intf mirror-2 for infinite seconds output in run-9a02571e8f02/scans/startup.pcap
MM dd hh:mm:ss network  INFO    Directing traffic for 9a:02:57:1e:8f:02 on port 2 to 2
MM dd hh:mm:ss faucetizer INFO    Reading structural config file: inst/faucet_intermediate.yaml
MM dd hh:mm:ss network  INFO    Waiting 5s for network to settle
MM dd hh:mm:ss runner   INFO    Port 1 dpid 2 learned 9a:02:57:1e:8f:01
MM dd hh:mm:ss runner   INFO    Gateway for device group 9a02571e8f01 not found, initializing base 1...
MM dd hh:mm:ss gateway  INFO    Initializing gateway 9a02571e8f01 as gw01/10
MM dd hh:mm:ss gateway  INFO    Added networking host gw01 on port 10 at 10.20.0.5
MM dd hh:mm:ss gateway  INFO    Added fake target fake01 on port 11 at 10.20.0.6
MM dd hh:mm:ss runner   INFO    Test ping gw01->fake01
MM dd hh:mm:ss runner   INFO    Test ping gw01->fake01
MM dd hh:mm:ss runner   INFO    Test ping fake01->gw01
MM dd hh:mm:ss runner   INFO    Test ping fake01->192.168.84.1
MM dd hh:mm:ss runner   INFO    Test ping gw01->fake01 from 192.168.84.1
MM dd hh:mm:ss gateway  INFO    Gateway 1 change lease time to 120s
MM dd hh:mm:ss gateway  INFO    Gateway 1 startup capture gw01-eth0 in container's /tmp/gateway.pcap
MM dd hh:mm:ss dhcp     INFO    DHCP monitor gw01 waiting for replies...
MM dd hh:mm:ss gateway  INFO    Attaching target 9a02571e8f01 to gateway group 9a02571e8f01
MM dd hh:mm:ss host     INFO    Loading device module config from /home/username/daq/local/site/mac_addrs/9a02571e8f01/device_config.json
MM dd hh:mm:ss host     INFO    Device config reloaded: True 9a02571e8f01 on port 1
MM dd hh:mm:ss config   INFO    Writing config to /home/username/daq/local/site/mac_addrs/9a02571e8f01/aux/module_config.json
MM dd hh:mm:ss host     INFO    Host 9a:02:57:1e:8f:01 running with enabled tests ['pass', 'fail', 'ping', 'bacnet', 'mudgee', 'nmap', 'discover']
MM dd hh:mm:ss report   INFO    Writing report to inst/reports/report_9a02571e8f01_2021-03-24T212342.*
MM dd hh:mm:ss report   INFO    Writing alternate report to local/site/mac_addrs/9a02571e8f01/report.*
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 initializing...
MM dd hh:mm:ss host     INFO    Loading base module config from /home/username/daq/local/site/mac_addrs/9a02571e8f01/base_config.json
MM dd hh:mm:ss network  INFO    Creating mirror pair mirror-1 <-> mirror-1-ext at 1001
MM dd hh:mm:ss host     INFO    Executing topology_hook: /home/username/daq/bin/dump_network inst/network
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 startup pcap capture
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 pcap intf mirror-1 for infinite seconds output in run-9a02571e8f01/scans/startup.pcap
MM dd hh:mm:ss network  INFO    Directing traffic for 9a:02:57:1e:8f:01 on port 1 to 1
MM dd hh:mm:ss faucetizer INFO    Reading structural config file: inst/faucet_intermediate.yaml
MM dd hh:mm:ss network  INFO    Waiting 5s for network to settle
MM dd hh:mm:ss runner   INFO    Port 30 dpid 1 learned e6:6f:00:90:4b:46 (ignored)
MM dd hh:mm:ss runner   INFO    Port 31 dpid 1 learned 5a:d1:76:51:b0:e2 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 5a:d1:76:51:b0:e2 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned e6:6f:00:90:4b:46 (ignored)
MM dd hh:mm:ss runner   INFO    System port 1 on dpid 1 is active True
MM dd hh:mm:ss runner   INFO    Port 1 dpid 2 learned 9a:02:57:1e:8f:01
MM dd hh:mm:ss runner   INFO    Port 3 dpid 2 learned 9a:02:57:1e:8f:03
MM dd hh:mm:ss runner   INFO    Port 1 dpid 1 learned 9a:02:57:1e:8f:03 (ignored)
MM dd hh:mm:ss runner   INFO    Port 20 dpid 1 learned 1e:ac:ac:76:b3:5b (ignored)
MM dd hh:mm:ss runner   INFO    Port 21 dpid 1 learned 1a:b3:72:c5:1c:d4 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 1e:ac:ac:76:b3:5b (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 1a:b3:72:c5:1c:d4 (ignored)
MM dd hh:mm:ss runner   INFO    Port 2 dpid 2 learned 9a:02:57:1e:8f:02
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 5a:d1:76:51:b0:e2 (ignored)
MM dd hh:mm:ss runner   INFO    Port 31 dpid 1 learned 5a:d1:76:51:b0:e2 (ignored)
MM dd hh:mm:ss runner   INFO    Port 1 dpid 1 learned 9a:02:57:1e:8f:02 (ignored)
MM dd hh:mm:ss runner   INFO    Port 2 dpid 2 learned 9a:02:57:1e:8f:02
MM dd hh:mm:ss runner   INFO    Port 10 dpid 1 learned 7e:d6:23:3f:7c:3b (ignored)
MM dd hh:mm:ss runner   INFO    Port 11 dpid 1 learned 1e:0c:b1:cd:6d:f5 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 7e:d6:23:3f:7c:3b (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 1e:0c:b1:cd:6d:f5 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 1a:b3:72:c5:1c:d4 (ignored)
MM dd hh:mm:ss runner   INFO    Port 1 dpid 2 learned 9a:02:57:1e:8f:01
MM dd hh:mm:ss runner   INFO    System port 1 on dpid 1 is active True
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 waiting for ip
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 using NORMAL DHCP mode, wait 0
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 waiting for ip
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 using NORMAL DHCP mode, wait 0
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 waiting for ip
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 using NORMAL DHCP mode, wait 0
MM dd hh:mm:ss runner   INFO    Port 11 dpid 1 learned 1e:0c:b1:cd:6d:f5 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 1e:0c:b1:cd:6d:f5 (ignored)
MM dd hh:mm:ss runner   INFO    Port 2 dpid 2 learned 9a:02:57:1e:8f:02
MM dd hh:mm:ss runner   INFO    Port 1 dpid 1 learned 9a:02:57:1e:8f:02 (ignored)
MM dd hh:mm:ss runner   INFO    Port 20 dpid 1 learned 1e:ac:ac:76:b3:5b (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 1e:ac:ac:76:b3:5b (ignored)
MM dd hh:mm:ss dhcp     INFO    DHCP monitor gw02 received Offer reply after 25s: 10.20.14.165/9a:02:57:1e:8f:02
MM dd hh:mm:ss runner   INFO    IP notify Offer 9a:02:57:1e:8f:02 is 10.20.14.165 on Gateway group 9a02571e8f02 set 2 (done/25)
MM dd hh:mm:ss dhcp     INFO    DHCP monitor gw02 received ACK reply after 25s: 10.20.14.165/9a:02:57:1e:8f:02
MM dd hh:mm:ss runner   INFO    IP notify ACK 9a:02:57:1e:8f:02 is 10.20.14.165 on Gateway group 9a02571e8f02 set 2 (done/25)
MM dd hh:mm:ss gateway  INFO    Ready target 9a02571e8f02 from gateway group 9a02571e8f02
MM dd hh:mm:ss gateway  INFO    Gateway 2 change lease time to 500s
MM dd hh:mm:ss runner   INFO    IP activating target 9a02571e8f02
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 triggered as 10.20.14.165
MM dd hh:mm:ss runner   INFO    Test ping gw02->10.20.14.165
MM dd hh:mm:ss runner   INFO    Test ping gw02->10.20.14.165
MM dd hh:mm:ss runner   INFO    Test ping gw02->10.20.14.165 from 192.168.84.2
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 done with base.
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 background pcap for 30s
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 pcap intf mirror-2 for 30 seconds output in run-9a02571e8f02/scans/monitor.pcap
MM dd hh:mm:ss runner   INFO    Port 21 dpid 1 learned 1a:b3:72:c5:1c:d4 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 1a:b3:72:c5:1c:d4 (ignored)
MM dd hh:mm:ss runner   INFO    Port 1 dpid 2 learned 9a:02:57:1e:8f:01
MM dd hh:mm:ss runner   INFO    Port 1 dpid 1 learned 9a:02:57:1e:8f:01 (ignored)
MM dd hh:mm:ss runner   INFO    Port 10 dpid 1 learned 7e:d6:23:3f:7c:3b (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 7e:d6:23:3f:7c:3b (ignored)
MM dd hh:mm:ss runner   INFO    Port 3 dpid 2 learned 9a:02:57:1e:8f:03
MM dd hh:mm:ss runner   INFO    Port 1 dpid 1 learned 9a:02:57:1e:8f:03 (ignored)
MM dd hh:mm:ss runner   INFO    Port 30 dpid 1 learned e6:6f:00:90:4b:46 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned e6:6f:00:90:4b:46 (ignored)
MM dd hh:mm:ss dhcp     INFO    DHCP monitor gw01 received Offer reply after 26s: 10.20.34.164/9a:02:57:1e:8f:01
MM dd hh:mm:ss runner   INFO    IP notify Offer 9a:02:57:1e:8f:01 is 10.20.34.164 on Gateway group 9a02571e8f01 set 1 (done/26)
MM dd hh:mm:ss dhcp     INFO    DHCP monitor gw01 received ACK reply after 26s: 10.20.34.164/9a:02:57:1e:8f:01
MM dd hh:mm:ss runner   INFO    IP notify ACK 9a:02:57:1e:8f:01 is 10.20.34.164 on Gateway group 9a02571e8f01 set 1 (done/26)
MM dd hh:mm:ss gateway  INFO    Ready target 9a02571e8f01 from gateway group 9a02571e8f01
MM dd hh:mm:ss gateway  INFO    Gateway 1 change lease time to 500s
MM dd hh:mm:ss runner   INFO    IP activating target 9a02571e8f01
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 triggered as 10.20.34.164
MM dd hh:mm:ss runner   INFO    Test ping gw01->10.20.34.164
MM dd hh:mm:ss runner   INFO    Test ping gw01->10.20.34.164
MM dd hh:mm:ss runner   INFO    Test ping gw01->10.20.34.164 from 192.168.84.1
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 done with base.
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 background pcap for 30s
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 pcap intf mirror-1 for 30 seconds output in run-9a02571e8f01/scans/monitor.pcap
MM dd hh:mm:ss dhcp     INFO    DHCP monitor gw03 received Offer reply after 56s: 10.20.79.166/9a:02:57:1e:8f:03
MM dd hh:mm:ss runner   INFO    IP notify Offer 9a:02:57:1e:8f:03 is 10.20.79.166 on Gateway group 9a02571e8f03 set 3 (done/56)
MM dd hh:mm:ss dhcp     INFO    DHCP monitor gw03 received ACK reply after 56s: 10.20.79.166/9a:02:57:1e:8f:03
MM dd hh:mm:ss runner   INFO    IP notify ACK 9a:02:57:1e:8f:03 is 10.20.79.166 on Gateway group 9a02571e8f03 set 3 (done/56)
MM dd hh:mm:ss gateway  INFO    Ready target 9a02571e8f03 from gateway group 9a02571e8f03
MM dd hh:mm:ss gateway  INFO    Gateway 3 change lease time to 500s
MM dd hh:mm:ss runner   INFO    IP activating target 9a02571e8f03
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 triggered as 10.20.79.166
MM dd hh:mm:ss runner   INFO    Test ping gw03->10.20.79.166
MM dd hh:mm:ss runner   INFO    Test ping gw03->10.20.79.166
MM dd hh:mm:ss runner   INFO    Test ping gw03->10.20.79.166 from 192.168.84.3
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 done with base.
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 background pcap for 30s
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 pcap intf mirror-3 for 30 seconds output in run-9a02571e8f03/scans/monitor.pcap
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 5a:d1:76:51:b0:e2 (ignored)
MM dd hh:mm:ss runner   INFO    Port 31 dpid 1 learned 5a:d1:76:51:b0:e2 (ignored)
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 start pass02
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f02/nodes/pass02/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 pcap intf mirror-2 for infinite seconds output in run-9a02571e8f02/scans/test_pass.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test pass mapping /home/username/daq/inst/config to /home/username/daq/inst/run-9a02571e8f02/test_root/config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test pass mapping /home/username/daq/local/site/mac_addrs/9a02571e8f02/aux to /home/username/daq/inst/run-9a02571e8f02/test_root/config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test pass mapping /home/username/daq/inst/gw02 to /home/username/daq/inst/run-9a02571e8f02/test_root/config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.14.165/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test pass running
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f02/finish/pass02
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test pass test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test pass passed 0.318385s
MM dd hh:mm:ss host     INFO    Host callback pass/pass02 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 start fail02
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f02/nodes/fail02/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 pcap intf mirror-2 for infinite seconds output in run-9a02571e8f02/scans/test_fail.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test fail mapping /home/username/daq/inst/config to /home/username/daq/inst/run-9a02571e8f02/test_root/config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test fail mapping /home/username/daq/local/site/mac_addrs/9a02571e8f02/aux to /home/username/daq/inst/run-9a02571e8f02/test_root/config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test fail mapping /home/username/daq/inst/gw02 to /home/username/daq/inst/run-9a02571e8f02/test_root/config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.14.165/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test fail running
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f02/finish/fail02
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test fail test host finalize 1
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test fail failed 0.334504s: 1 None
MM dd hh:mm:ss host     INFO    Host callback fail/fail02 was 1 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 start ping02
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f02/nodes/ping02/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 pcap intf mirror-2 for infinite seconds output in run-9a02571e8f02/scans/test_ping.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test ping mapping /home/username/daq/inst/config to /home/username/daq/inst/run-9a02571e8f02/test_root/config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test ping mapping /home/username/daq/local/site/mac_addrs/9a02571e8f02/aux to /home/username/daq/inst/run-9a02571e8f02/test_root/config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test ping mapping /home/username/daq/inst/gw02 to /home/username/daq/inst/run-9a02571e8f02/test_root/config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.14.165/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test ping running
MM dd hh:mm:ss runner   INFO    Port 22 dpid 1 learned fe:2a:91:c0:34:48 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned fe:2a:91:c0:34:48 (ignored)
MM dd hh:mm:ss runner   INFO    Port 22 dpid 1 learned 16:e7:a2:8e:42:2f (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 16:e7:a2:8e:42:2f (ignored)
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f02/finish/ping02
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test ping test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test ping passed 9.569871s
MM dd hh:mm:ss host     INFO    Host callback ping/ping02 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 start bacnet02
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f02/nodes/bacnet02/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 pcap intf mirror-2 for infinite seconds output in run-9a02571e8f02/scans/test_bacnet.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test bacnet mapping /home/username/daq/inst/config to /config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test bacnet mapping /home/username/daq/local/site/mac_addrs/9a02571e8f02/aux to /config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test bacnet mapping /home/username/daq/inst/gw02 to /config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.14.165/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test bacnet running
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f02/finish/bacnet02
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test bacnet test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test bacnet passed 2.986135s
MM dd hh:mm:ss host     INFO    Host callback bacnet/bacnet02 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 start mudgee02
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f02/nodes/mudgee02/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 pcap intf mirror-2 for infinite seconds output in run-9a02571e8f02/scans/test_mudgee.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test mudgee mapping /home/username/daq/inst/config to /config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test mudgee mapping /home/username/daq/local/site/mac_addrs/9a02571e8f02/aux to /config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test mudgee mapping /home/username/daq/inst/gw02 to /config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.14.165/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test mudgee running
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 start pass01
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f01/nodes/pass01/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 pcap intf mirror-1 for infinite seconds output in run-9a02571e8f01/scans/test_pass.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test pass mapping /home/username/daq/inst/config to /home/username/daq/inst/run-9a02571e8f01/test_root/config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test pass mapping /home/username/daq/local/site/mac_addrs/9a02571e8f01/aux to /home/username/daq/inst/run-9a02571e8f01/test_root/config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test pass mapping /home/username/daq/inst/gw01 to /home/username/daq/inst/run-9a02571e8f01/test_root/config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.34.164/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test pass running
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f01/finish/pass01
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test pass test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test pass passed 0.349835s
MM dd hh:mm:ss host     INFO    Host callback pass/pass01 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 start fail01
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f01/nodes/fail01/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 pcap intf mirror-1 for infinite seconds output in run-9a02571e8f01/scans/test_fail.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test fail mapping /home/username/daq/inst/config to /home/username/daq/inst/run-9a02571e8f01/test_root/config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test fail mapping /home/username/daq/local/site/mac_addrs/9a02571e8f01/aux to /home/username/daq/inst/run-9a02571e8f01/test_root/config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test fail mapping /home/username/daq/inst/gw01 to /home/username/daq/inst/run-9a02571e8f01/test_root/config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.34.164/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test fail running
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f01/finish/fail01
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test fail test host finalize 1
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test fail failed 0.307136s: 1 None
MM dd hh:mm:ss host     INFO    Host callback fail/fail01 was 1 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 start ping01
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f01/nodes/ping01/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 pcap intf mirror-1 for infinite seconds output in run-9a02571e8f01/scans/test_ping.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test ping mapping /home/username/daq/inst/config to /home/username/daq/inst/run-9a02571e8f01/test_root/config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test ping mapping /home/username/daq/local/site/mac_addrs/9a02571e8f01/aux to /home/username/daq/inst/run-9a02571e8f01/test_root/config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test ping mapping /home/username/daq/inst/gw01 to /home/username/daq/inst/run-9a02571e8f01/test_root/config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.34.164/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test ping running
MM dd hh:mm:ss runner   INFO    Port 12 dpid 1 learned d6:d0:13:ac:43:21 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned d6:d0:13:ac:43:21 (ignored)
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f02/finish/mudgee02
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test mudgee test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test mudgee passed 3.327186s
MM dd hh:mm:ss host     INFO    Host callback mudgee/mudgee02 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 start nmap02
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f02/nodes/nmap02/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 pcap intf mirror-2 for infinite seconds output in run-9a02571e8f02/scans/test_nmap.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test nmap mapping /home/username/daq/inst/config to /home/username/daq/inst/run-9a02571e8f02/test_root/config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test nmap mapping /home/username/daq/local/site/mac_addrs/9a02571e8f02/aux to /home/username/daq/inst/run-9a02571e8f02/test_root/config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test nmap mapping /home/username/daq/inst/gw02 to /home/username/daq/inst/run-9a02571e8f02/test_root/config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.14.165/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test nmap running
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 start pass03
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f03/nodes/pass03/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 pcap intf mirror-3 for infinite seconds output in run-9a02571e8f03/scans/test_pass.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test pass mapping /home/username/daq/inst/config to /home/username/daq/inst/run-9a02571e8f03/test_root/config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test pass mapping /home/username/daq/local/site/mac_addrs/9a02571e8f03/aux to /home/username/daq/inst/run-9a02571e8f03/test_root/config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test pass mapping /home/username/daq/inst/gw03 to /home/username/daq/inst/run-9a02571e8f03/test_root/config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.79.166/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test pass running
MM dd hh:mm:ss runner   INFO    Port 22 dpid 1 learned 4e:c3:88:de:10:bd (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 4e:c3:88:de:10:bd (ignored)
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f03/finish/pass03
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test pass test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test pass passed 0.308866s
MM dd hh:mm:ss host     INFO    Host callback pass/pass03 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 start fail03
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f03/nodes/fail03/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 pcap intf mirror-3 for infinite seconds output in run-9a02571e8f03/scans/test_fail.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test fail mapping /home/username/daq/inst/config to /home/username/daq/inst/run-9a02571e8f03/test_root/config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test fail mapping /home/username/daq/local/site/mac_addrs/9a02571e8f03/aux to /home/username/daq/inst/run-9a02571e8f03/test_root/config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test fail mapping /home/username/daq/inst/gw03 to /home/username/daq/inst/run-9a02571e8f03/test_root/config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.79.166/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test fail running
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f03/finish/fail03
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test fail test host finalize 1
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test fail failed 0.282681s: 1 None
MM dd hh:mm:ss host     INFO    Host callback fail/fail03 was 1 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 start ping03
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f03/nodes/ping03/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 pcap intf mirror-3 for infinite seconds output in run-9a02571e8f03/scans/test_ping.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test ping mapping /home/username/daq/inst/config to /home/username/daq/inst/run-9a02571e8f03/test_root/config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test ping mapping /home/username/daq/local/site/mac_addrs/9a02571e8f03/aux to /home/username/daq/inst/run-9a02571e8f03/test_root/config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test ping mapping /home/username/daq/inst/gw03 to /home/username/daq/inst/run-9a02571e8f03/test_root/config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.79.166/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test ping running
MM dd hh:mm:ss dhcp     INFO    DHCP monitor gw02 received ACK reply after 51s: 10.20.14.165/9a:02:57:1e:8f:02
MM dd hh:mm:ss runner   INFO    IP notify ACK 9a:02:57:1e:8f:02 is 10.20.14.165 on Gateway group 9a02571e8f02 set 2 (done/51)
MM dd hh:mm:ss runner   INFO    DHCP activation group 9a02571e8f02 already activated
MM dd hh:mm:ss runner   INFO    Port 32 dpid 1 learned c2:73:ca:b9:06:d4 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned c2:73:ca:b9:06:d4 (ignored)
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f01/finish/ping01
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test ping test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test ping passed 9.598075s
MM dd hh:mm:ss host     INFO    Host callback ping/ping01 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 start bacnet01
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f01/nodes/bacnet01/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 pcap intf mirror-1 for infinite seconds output in run-9a02571e8f01/scans/test_bacnet.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test bacnet mapping /home/username/daq/inst/config to /config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test bacnet mapping /home/username/daq/local/site/mac_addrs/9a02571e8f01/aux to /config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test bacnet mapping /home/username/daq/inst/gw01 to /config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.34.164/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test bacnet running
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f01/finish/bacnet01
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test bacnet test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test bacnet passed 1.466708s
MM dd hh:mm:ss host     INFO    Host callback bacnet/bacnet01 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 start mudgee01
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f01/nodes/mudgee01/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 pcap intf mirror-1 for infinite seconds output in run-9a02571e8f01/scans/test_mudgee.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test mudgee mapping /home/username/daq/inst/config to /config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test mudgee mapping /home/username/daq/local/site/mac_addrs/9a02571e8f01/aux to /config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test mudgee mapping /home/username/daq/inst/gw01 to /config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.34.164/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test mudgee running
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f03/finish/ping03
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test ping test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test ping passed 9.80309s
MM dd hh:mm:ss host     INFO    Host callback ping/ping03 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 start bacnet03
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f03/nodes/bacnet03/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 pcap intf mirror-3 for infinite seconds output in run-9a02571e8f03/scans/test_bacnet.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test bacnet mapping /home/username/daq/inst/config to /config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test bacnet mapping /home/username/daq/local/site/mac_addrs/9a02571e8f03/aux to /config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test bacnet mapping /home/username/daq/inst/gw03 to /config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.79.166/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test bacnet running
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f01/finish/mudgee01
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test mudgee test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test mudgee passed 2.686918s
MM dd hh:mm:ss host     INFO    Host callback mudgee/mudgee01 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 start nmap01
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f01/nodes/nmap01/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 pcap intf mirror-1 for infinite seconds output in run-9a02571e8f01/scans/test_nmap.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test nmap mapping /home/username/daq/inst/config to /home/username/daq/inst/run-9a02571e8f01/test_root/config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test nmap mapping /home/username/daq/local/site/mac_addrs/9a02571e8f01/aux to /home/username/daq/inst/run-9a02571e8f01/test_root/config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test nmap mapping /home/username/daq/inst/gw01 to /home/username/daq/inst/run-9a02571e8f01/test_root/config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.34.164/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test nmap running
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f03/finish/bacnet03
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test bacnet test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test bacnet passed 2.235677s
MM dd hh:mm:ss host     INFO    Host callback bacnet/bacnet03 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 start mudgee03
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f03/nodes/mudgee03/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 pcap intf mirror-3 for infinite seconds output in run-9a02571e8f03/scans/test_mudgee.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test mudgee mapping /home/username/daq/inst/config to /config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test mudgee mapping /home/username/daq/local/site/mac_addrs/9a02571e8f03/aux to /config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test mudgee mapping /home/username/daq/inst/gw03 to /config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.79.166/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test mudgee running
MM dd hh:mm:ss runner   INFO    Port 12 dpid 1 learned 3e:f9:ff:09:9c:cd (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 3e:f9:ff:09:9c:cd (ignored)
MM dd hh:mm:ss dhcp     INFO    DHCP monitor gw03 received ACK reply after 47s: 10.20.79.166/9a:02:57:1e:8f:03
MM dd hh:mm:ss runner   INFO    IP notify ACK 9a:02:57:1e:8f:03 is 10.20.79.166 on Gateway group 9a02571e8f03 set 3 (done/47)
MM dd hh:mm:ss runner   INFO    DHCP activation group 9a02571e8f03 already activated
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f03/finish/mudgee03
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test mudgee test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test mudgee passed 2.001876s
MM dd hh:mm:ss host     INFO    Host callback mudgee/mudgee03 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 start nmap03
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f03/nodes/nmap03/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 pcap intf mirror-3 for infinite seconds output in run-9a02571e8f03/scans/test_nmap.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test nmap mapping /home/username/daq/inst/config to /home/username/daq/inst/run-9a02571e8f03/test_root/config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test nmap mapping /home/username/daq/local/site/mac_addrs/9a02571e8f03/aux to /home/username/daq/inst/run-9a02571e8f03/test_root/config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test nmap mapping /home/username/daq/inst/gw03 to /home/username/daq/inst/run-9a02571e8f03/test_root/config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.79.166/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test nmap running
MM dd hh:mm:ss runner   INFO    Port 32 dpid 1 learned 7a:c0:97:a3:32:f2 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 7a:c0:97:a3:32:f2 (ignored)
MM dd hh:mm:ss dhcp     INFO    DHCP monitor gw01 received ACK reply after 51s: 10.20.34.164/9a:02:57:1e:8f:01
MM dd hh:mm:ss runner   INFO    IP notify ACK 9a:02:57:1e:8f:01 is 10.20.34.164 on Gateway group 9a02571e8f01 set 1 (done/51)
MM dd hh:mm:ss runner   INFO    DHCP activation group 9a02571e8f01 already activated
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f02/finish/nmap02
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test nmap test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test nmap passed 51.878767s
MM dd hh:mm:ss host     INFO    Host callback nmap/nmap02 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 start discover02
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f02/nodes/discover02/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 pcap intf mirror-2 for infinite seconds output in run-9a02571e8f02/scans/test_discover.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test discover mapping /home/username/daq/inst/config to /config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test discover mapping /home/username/daq/local/site/mac_addrs/9a02571e8f02/aux to /config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test discover mapping /home/username/daq/inst/gw02 to /config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.14.165/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test discover running
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 4e:95:60:3b:7b:3e (ignored)
MM dd hh:mm:ss runner   INFO    Port 22 dpid 1 learned 4e:95:60:3b:7b:3e (ignored)
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f02/finish/discover02
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test discover test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f02 test discover passed 5.0054s
MM dd hh:mm:ss host     INFO    Host callback discover/discover02 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 no more tests remaining
MM dd hh:mm:ss runner   INFO    Target device 9a:02:57:1e:8f:02 cancel (#3/0).
MM dd hh:mm:ss network  INFO    Directing traffic for 9a:02:57:1e:8f:02 on port 2 to None
MM dd hh:mm:ss faucetizer INFO    Reading structural config file: inst/faucet_intermediate.yaml
MM dd hh:mm:ss network  INFO    Waiting 5s for network to settle
MM dd hh:mm:ss gateway  INFO    Detach target 9a02571e8f02 from gateway group 9a02571e8f02: ['9a:02:57:1e:8f:02']
MM dd hh:mm:ss runner   INFO    Retiring Gateway group 9a02571e8f02 set 2. Last device: 9a02571e8f02
MM dd hh:mm:ss gateway  INFO    Terminating gateway 2/9a02571e8f02
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f02 on port 2 terminate, running unknown, trigger False: _target_set_cancel
MM dd hh:mm:ss network  INFO    Deleting mirror pair mirror-2 <-> mirror-2-ext
MM dd hh:mm:ss report   INFO    Finalizing report_9a02571e8f02_2021-03-24T212329
MM dd hh:mm:ss report   INFO    Skipping missing report header template local/site/report_template.md
MM dd hh:mm:ss report   INFO    Copying test report inst/run-9a02571e8f02/nodes/ping02/tmp/report.txt
MM dd hh:mm:ss report   INFO    Copying test report inst/run-9a02571e8f02/nodes/nmap02/tmp/report.txt
MM dd hh:mm:ss report   INFO    Copying test report inst/run-9a02571e8f02/nodes/discover02/tmp/report.txt
MM dd hh:mm:ss report   INFO    Generating HTML for writing pdf report...
MM dd hh:mm:ss report   INFO    Metamorphosising HTML to PDF...
MM dd hh:mm:ss weasyprint WARNING Expected a media type, got only/**/screen/**/and/**/(min-width: 480px)
MM dd hh:mm:ss weasyprint WARNING Invalid media type " only screen and (min-width: 480px) " the whole @media rule was ignored at 231:1.
MM dd hh:mm:ss weasyprint WARNING Expected a media type, got only/**/screen/**/and/**/(min-width: 768px)
MM dd hh:mm:ss weasyprint WARNING Invalid media type " only screen and (min-width: 768px) " the whole @media rule was ignored at 236:1.
MM dd hh:mm:ss report   INFO    Copying reports to local/site/mac_addrs/9a02571e8f02/report.*
MM dd hh:mm:ss host     INFO    Finalized with reports ['report_path.md', 'report_path.pdf', 'report_path.json', 'trigger_path']
MM dd hh:mm:ss runner   INFO    Target device 9a02571e8f02 finalize: [] (target set not active)
MM dd hh:mm:ss runner   WARNING Suppressing future tests because test done in single shot.
MM dd hh:mm:ss runner   INFO    System port 1 on dpid 1 is active True
MM dd hh:mm:ss runner   INFO    Port 12 dpid 1 learned 3e:f9:ff:09:9c:cd (ignored)
MM dd hh:mm:ss runner   INFO    Port 32 dpid 1 learned 7a:c0:97:a3:32:f2 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 7a:c0:97:a3:32:f2 (ignored)
MM dd hh:mm:ss runner   INFO    Port 3 dpid 2 learned 9a:02:57:1e:8f:03
MM dd hh:mm:ss runner   INFO    Port 1 dpid 2 learned 9a:02:57:1e:8f:01
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 3e:f9:ff:09:9c:cd (ignored)
MM dd hh:mm:ss runner   INFO    Port 1 dpid 1 learned 9a:02:57:1e:8f:03 (ignored)
MM dd hh:mm:ss runner   INFO    Port 1 dpid 1 learned 9a:02:57:1e:8f:01 (ignored)
MM dd hh:mm:ss runner   INFO    Port 2 dpid 2 learned 9a:02:57:1e:8f:02
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned 1e:ac:ac:76:b3:5b (ignored)
MM dd hh:mm:ss runner   INFO    Remaining target sets: [9a02571e8f03, 9a02571e8f01]
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f01/finish/nmap01
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test nmap test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test nmap passed 52.77895s
MM dd hh:mm:ss host     INFO    Host callback nmap/nmap01 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 start discover01
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f01/nodes/discover01/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 pcap intf mirror-1 for infinite seconds output in run-9a02571e8f01/scans/test_discover.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test discover mapping /home/username/daq/inst/config to /config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test discover mapping /home/username/daq/local/site/mac_addrs/9a02571e8f01/aux to /config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test discover mapping /home/username/daq/inst/gw01 to /config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.34.164/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test discover running
MM dd hh:mm:ss runner   INFO    Port 20 dpid 1 learned 1e:ac:ac:76:b3:5b (ignored)
MM dd hh:mm:ss runner   INFO    Port 12 dpid 1 learned ea:a9:d7:3c:08:f6 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned ea:a9:d7:3c:08:f6 (ignored)
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f03/finish/nmap03
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test nmap test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test nmap passed 51.546848s
MM dd hh:mm:ss host     INFO    Host callback nmap/nmap03 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 start discover03
MM dd hh:mm:ss config   INFO    Writing config to inst/run-9a02571e8f03/nodes/discover03/tmp/module_config.json
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 pcap intf mirror-3 for infinite seconds output in run-9a02571e8f03/scans/test_discover.pcap
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test discover mapping /home/username/daq/inst/config to /config/inst
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test discover mapping /home/username/daq/local/site/mac_addrs/9a02571e8f03/aux to /config/device
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test discover mapping /home/username/daq/inst/gw03 to /config/gw
MM dd hh:mm:ss exmodule INFO    Target subnet 10.20.79.166/32 overlaps with runner subnet 10.20.0.0/16.
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test discover running
MM dd hh:mm:ss runner   INFO    Port 32 dpid 1 learned c2:f0:f1:e6:f3:07 (ignored)
MM dd hh:mm:ss runner   INFO    Port 4 dpid 2 learned c2:f0:f1:e6:f3:07 (ignored)
MM dd hh:mm:ss runner   INFO    Port 10 dpid 1 learned 7e:d6:23:3f:7c:3b (ignored)
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f01/finish/discover01
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test discover test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f01 test discover passed 4.167411s
MM dd hh:mm:ss host     INFO    Host callback discover/discover01 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 no more tests remaining
MM dd hh:mm:ss runner   INFO    Target device 9a:02:57:1e:8f:01 cancel (#3/0).
MM dd hh:mm:ss network  INFO    Directing traffic for 9a:02:57:1e:8f:01 on port 1 to None
MM dd hh:mm:ss faucetizer INFO    Reading structural config file: inst/faucet_intermediate.yaml
MM dd hh:mm:ss network  INFO    Waiting 5s for network to settle
MM dd hh:mm:ss gateway  INFO    Detach target 9a02571e8f01 from gateway group 9a02571e8f01: ['9a:02:57:1e:8f:01']
MM dd hh:mm:ss runner   INFO    Retiring Gateway group 9a02571e8f01 set 1. Last device: 9a02571e8f01
MM dd hh:mm:ss gateway  INFO    Terminating gateway 1/9a02571e8f01
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f01 on port 1 terminate, running unknown, trigger False: _target_set_cancel
MM dd hh:mm:ss network  INFO    Deleting mirror pair mirror-1 <-> mirror-1-ext
MM dd hh:mm:ss report   INFO    Finalizing report_9a02571e8f01_2021-03-24T212342
MM dd hh:mm:ss report   INFO    Skipping missing report header template local/site/report_template.md
MM dd hh:mm:ss report   INFO    Copying test report inst/run-9a02571e8f01/nodes/ping01/tmp/report.txt
MM dd hh:mm:ss report   INFO    Copying test report inst/run-9a02571e8f01/nodes/nmap01/tmp/report.txt
MM dd hh:mm:ss report   INFO    Copying test report inst/run-9a02571e8f01/nodes/discover01/tmp/report.txt
MM dd hh:mm:ss report   INFO    Generating HTML for writing pdf report...
MM dd hh:mm:ss report   INFO    Metamorphosising HTML to PDF...
MM dd hh:mm:ss weasyprint WARNING Expected a media type, got only/**/screen/**/and/**/(min-width: 480px)
MM dd hh:mm:ss weasyprint WARNING Invalid media type " only screen and (min-width: 480px) " the whole @media rule was ignored at 231:1.
MM dd hh:mm:ss weasyprint WARNING Expected a media type, got only/**/screen/**/and/**/(min-width: 768px)
MM dd hh:mm:ss weasyprint WARNING Invalid media type " only screen and (min-width: 768px) " the whole @media rule was ignored at 236:1.
MM dd hh:mm:ss report   INFO    Copying reports to local/site/mac_addrs/9a02571e8f01/report.*
MM dd hh:mm:ss host     INFO    Finalized with reports ['report_path.md', 'report_path.pdf', 'report_path.json', 'trigger_path']
MM dd hh:mm:ss runner   INFO    Target device 9a02571e8f01 finalize: [] (target set not active)
MM dd hh:mm:ss runner   INFO    Remaining target sets: [9a02571e8f03]
MM dd hh:mm:ss runner   INFO    Port 30 dpid 1 learned e6:6f:00:90:4b:46 (ignored)
MM dd hh:mm:ss runner   INFO    Port 2 dpid 2 learned 9a:02:57:1e:8f:02
MM dd hh:mm:ss runner   INFO    Port 1 dpid 2 learned 9a:02:57:1e:8f:01
MM dd hh:mm:ss host     INFO    Executing finish_hook: /home/username/daq/bin/dump_network inst/run-9a02571e8f03/finish/discover03
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test discover test host finalize 0
MM dd hh:mm:ss exmodule INFO    Target device 9a02571e8f03 test discover passed 8.904613s
MM dd hh:mm:ss host     INFO    Host callback discover/discover03 was 0 with None
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 network pcap complete
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 no more tests remaining
MM dd hh:mm:ss runner   INFO    Target device 9a:02:57:1e:8f:03 cancel (#3/0).
MM dd hh:mm:ss network  INFO    Directing traffic for 9a:02:57:1e:8f:03 on port 3 to None
MM dd hh:mm:ss faucetizer INFO    Reading structural config file: inst/faucet_intermediate.yaml
MM dd hh:mm:ss network  INFO    Waiting 5s for network to settle
MM dd hh:mm:ss gateway  INFO    Detach target 9a02571e8f03 from gateway group 9a02571e8f03: ['9a:02:57:1e:8f:03']
MM dd hh:mm:ss runner   INFO    Retiring Gateway group 9a02571e8f03 set 3. Last device: 9a02571e8f03
MM dd hh:mm:ss gateway  INFO    Terminating gateway 3/9a02571e8f03
MM dd hh:mm:ss host     INFO    Target device 9a02571e8f03 on port 3 terminate, running unknown, trigger False: _target_set_cancel
MM dd hh:mm:ss network  INFO    Deleting mirror pair mirror-3 <-> mirror-3-ext
MM dd hh:mm:ss report   INFO    Finalizing report_9a02571e8f03_2021-03-24T212315
MM dd hh:mm:ss report   INFO    Skipping missing report header template local/site/report_template.md
MM dd hh:mm:ss report   INFO    Copying test report inst/run-9a02571e8f03/nodes/ping03/tmp/report.txt
MM dd hh:mm:ss report   INFO    Copying test report inst/run-9a02571e8f03/nodes/nmap03/tmp/report.txt
MM dd hh:mm:ss report   INFO    Copying test report inst/run-9a02571e8f03/nodes/discover03/tmp/report.txt
MM dd hh:mm:ss report   INFO    Generating HTML for writing pdf report...
MM dd hh:mm:ss report   INFO    Metamorphosising HTML to PDF...
MM dd hh:mm:ss weasyprint WARNING Expected a media type, got only/**/screen/**/and/**/(min-width: 480px)
MM dd hh:mm:ss weasyprint WARNING Invalid media type " only screen and (min-width: 480px) " the whole @media rule was ignored at 231:1.
MM dd hh:mm:ss weasyprint WARNING Expected a media type, got only/**/screen/**/and/**/(min-width: 768px)
MM dd hh:mm:ss weasyprint WARNING Invalid media type " only screen and (min-width: 768px) " the whole @media rule was ignored at 236:1.
MM dd hh:mm:ss report   INFO    Copying reports to local/site/mac_addrs/9a02571e8f03/report.*
MM dd hh:mm:ss host     INFO    Finalized with reports ['report_path.md', 'report_path.pdf', 'report_path.json', 'trigger_path']
MM dd hh:mm:ss runner   INFO    Target device 9a02571e8f03 finalize: [] (target set not active)
MM dd hh:mm:ss runner   INFO    Remaining target sets: []
MM dd hh:mm:ss stream   INFO    Monitoring 0 fds 
MM dd hh:mm:ss runner   WARNING No active ports remaining (0 monitors), ending test run.
MM dd hh:mm:ss runner   INFO    Stopping network...
MM dd hh:mm:ss mininet  INFO    *** Stopping 2 controllers
MM dd hh:mm:ss mininet  INFO    faucet
MM dd hh:mm:ss mininet  INFO    gauge
MM dd hh:mm:ss mininet  INFO    *** Stopping 1 links
MM dd hh:mm:ss mininet  INFO    .
MM dd hh:mm:ss mininet  INFO    *** Stopping 2 switches
MM dd hh:mm:ss mininet  INFO    pri
MM dd hh:mm:ss mininet  INFO    sec
MM dd hh:mm:ss mininet  INFO    *** Stopping 1 hosts
MM dd hh:mm:ss mininet  INFO    gw03
MM dd hh:mm:ss mininet  INFO    *** Done
MM dd hh:mm:ss runner   INFO    Done with runner.
MM dd hh:mm:ss daq      INFO    DAQ runner returned 0
Cleanup docker cp daq-usi:/root/logs.txt inst/cmdusi.log
Cleanup docker kill daq-usi
daq-usi
Cleanup docker kill daq-faux-1
daq-faux-1
Cleanup docker kill daq-faux-2
daq-faux-2
Cleanup docker kill daq-faux-3
daq-faux-3
Done with run, exit 0
</pre>
