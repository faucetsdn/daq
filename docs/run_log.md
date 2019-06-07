<pre>
username@hostname:~/daq$ <b>mkdir -p local</b>
username@hostname:~/daq$ <b>cp misc/system_all.conf local/system.conf</b>
username@hostname:~/daq$ <b>cmd/run -s</b>
Activating venv
Loading config from local/system.conf
Starting Thu Jun 6 20:17:51 PDT 2019, run_mode is local.
Clearing previous state...
Running as root...
Activating venv
Loading config from local/system.conf
Release version 0.9.7
ovsdb-server is running with pid 4425
ovs-vswitchd is running with pid 172623
Creating mudacl templates...
Starting a Gradle Daemon (subsequent builds will be faster)
:compileJava UP-TO-DATE
:processResources NO-SOURCE
:classes UP-TO-DATE
:shadowJar UP-TO-DATE

BUILD SUCCESSFUL in 3s
2 actionable tasks: 2 up-to-date
Running mudacl regression test...
Writing output files to /home/username/daq/mudacl/out/acl_templates
Writing output files to /home/username/daq/mudacl/out/port_acls
Compare out/acl_templates/ with setup/acl_templates/...
Compare out/port_acls/ with setup/port_acls/...
Activating venv
Loading config from local/system.conf
:compileJava UP-TO-DATE
:processResources NO-SOURCE
:classes UP-TO-DATE
:shadowJar UP-TO-DATE

BUILD SUCCESSFUL in 0s
2 actionable tasks: 2 up-to-date

Executing mudacl generator on mud_files/...
Writing output files to /home/username/daq/inst/acl_templates
inst/acl_templates:
total 40
-rw-r--r-- 1 root root  540 Jun  6 20:01 template_bacnet_acl.yaml
-rw-r--r-- 1 root root  332 Jun  6 20:01 template_bacnet_frdev_acl.yaml
-rw-r--r-- 1 root root  332 Jun  6 20:01 template_bacnet_todev_acl.yaml
-rw-r--r-- 1 root root  768 Jun  6 20:01 template_baseline_acl.yaml
-rw-r--r-- 1 root root 1966 Jun  6 20:01 template_commissioning_acl.yaml
-rw-r--r-- 1 root root 1452 Jun  6 20:01 template_controller_acl.yaml
-rw-r--r-- 1 root root   78 Jun  6 20:01 template_default_acl.yaml
-rw-r--r-- 1 root root 1442 Jun  6 20:01 template_lightbulb_acl.yaml
-rw-r--r-- 1 root root  258 Jun  6 20:01 template_raw_acl.yaml
-rw-r--r-- 1 root root  496 Jun  6 20:01 template_telnet_acl.yaml

inst/port_acls:
total 0
Sourcing misc/startup_multi.cmd...
DAQ autostart cmd/faux 1
Activating venv
Loading config from local/system.conf
Launching faux ...
Clensing old container daq-faux-1
DAQ autoclean docker kill daq-faux-1
Removing old interface faux-1
Adding new interface to 231107...
Done with faux device launch.
DAQ autostart cmd/faux 2
Activating venv
Loading config from local/system.conf
Launching faux ...
Clensing old container daq-faux-2
DAQ autoclean docker kill daq-faux-2
Removing old interface faux-2
Adding new interface to 231385...
Done with faux device launch.
DAQ autostart cmd/faux 3
Activating venv
Loading config from local/system.conf
Launching faux ...
Clensing old container daq-faux-3
DAQ autoclean docker kill daq-faux-3
Removing old interface faux-3
Adding new interface to 231709...
Done with faux device launch.
Entering virtual python environment...
Using python3 at /home/username/daq/venv/bin/python3
Executing: python3 -u daq/daq.py /home/username/daq/local/system.conf -s
Prepending /home/username/daq/binhack to PATH
processing arg: /home/username/daq/local/system.conf
Reading config from /home/username/daq/local/system.conf
Reading config from misc/system.conf
processing arg: -s
base_conf=misc/module_config.json
host_tests=misc/all_tests.conf
intf_names=faux-1,faux-2,faux-3
run_mode=local
schema_path=schemas/udmi/
sec_port=4
single_shot=True
site_description="Multi-Device All-Tests Configuration"
site_path=local/site/
startup_cmds=misc/startup_multi.cmd
INFO:daq:pid is 231826
INFO:gcp:No gcp_cred credential specified in config
INFO:config:Loading config from misc/module_config.json
INFO:config:Skipping missing local/site/module_config.json
INFO:runner:Reading test definition file misc/all_tests.conf
INFO:runner:Reading test definition file misc/host_tests.conf
INFO:runner:Reading test definition file subset/pentests/build.conf
INFO:runner:Reading test definition file subset/switches/build.conf
INFO:runner:Reading test definition file subset/connection/build.conf
INFO:runner:Reading test definition file subset/bacnet/build.conf
INFO:runner:Reading test definition file subset/security/build.conf
INFO:runner:Configured with tests ['pass', 'fail', 'ping', 'bacnet', 'mudgee', 'nmap', 'brute', 'switch', 'macoui', 'bacext', 'tls']
INFO:network:Activating faucet topology...
INFO:topology:No device_specs file specified, skipping...
INFO:topology:Writing network config to inst/faucet.yaml
INFO:topology:Starting faucet...
INFO:network:Creating ovs sec with dpid/port 2/4
INFO:network:Added switch link pri-eth1 <-> sec-eth4
INFO:network:Attaching device interface faux-1 on port 1.
INFO:network:Attaching device interface faux-2 on port 2.
INFO:network:Attaching device interface faux-3 on port 3.
INFO:network:Starting mininet...
INFO:mininet:*** Configuring hosts
INFO:mininet:*** Starting controller
INFO:mininet:controller
INFO:mininet:*** Starting 2 switches
INFO:mininet:pri
INFO:mininet:sec
INFO:mininet:...
INFO:runner:Waiting for system to settle...
INFO:runner:Entering main event loop.
INFO:runner:If this blocks for too long, see docs/test_lab.md for tips and tricks.
INFO:runner:System port 4 on dpid 2 is active True
INFO:runner:Port 3 dpid 2 is now active True
INFO:runner:Port 2 dpid 2 is now active True
INFO:runner:Port 1 dpid 2 is now active True
INFO:runner:Port 1 dpid 2 learned 9a:02:57:1e:8f:01
INFO:runner:Gateway for device group 9a02571e8f01 not found, initializing base 1...
INFO:gateway:Initializing gateway 9a02571e8f01 as gw01/10
INFO:gateway:Added networking host gw01 on port 10 at 10.0.0.1
INFO:gateway:Added dummy target dummy01 on port 11 at 10.0.0.2
INFO:gateway:Gateway 1 startup capture gw01-eth0 in container's /tmp/gateway.pcap
INFO:dhcp:DHCP monitor gw01 waiting for replies...
INFO:runner:Test ping gw01->dummy01
INFO:runner:Test ping gw01->dummy01
INFO:runner:Test ping dummy01->gw01
INFO:runner:Test ping dummy01->192.168.84.1
INFO:runner:Test ping gw01->dummy01 from 192.168.84.1
INFO:gateway:Attaching target 1 to gateway group 9a02571e8f01
INFO:config:Loading config from /home/username/daq/local/site/mac_addrs/9a02571e8f01/module_config.json
INFO:host:Device config reloaded: True 9a:02:57:1e:8f:01
INFO:host:Host 1 running with enabled tests ['pass', 'fail', 'ping', 'nmap', 'brute', 'switch', 'macoui', 'bacext', 'tls']
INFO:report:Creating report as inst/reports/report_9a02571e8f01_2019-06-07T030147+0000.md
INFO:report:Skipping missing report header template local/site/report_template.md
INFO:runner:Target port 1 registered 9a:02:57:1e:8f:01
INFO:host:Target port 1 initializing...
INFO:config:Loading config from /home/username/daq/local/site/mac_addrs/9a02571e8f01/module_config.json
INFO:network:Creating mirror pair mirror-1 <-> mirror-1-ext at 1001
INFO:host:Target port 1 startup pcap capture
INFO:network:Directing traffic for 9a:02:57:1e:8f:01 on port 1: True
INFO:topology:Waiting 5s for network to settle
INFO:runner:Port 2 dpid 2 learned 9a:02:57:1e:8f:02
INFO:runner:Gateway for device group 9a02571e8f02 not found, initializing base 2...
INFO:gateway:Initializing gateway 9a02571e8f02 as gw02/20
INFO:gateway:Added networking host gw02 on port 20 at 10.0.0.3
INFO:gateway:Added dummy target dummy02 on port 21 at 10.0.0.4
INFO:gateway:Gateway 2 startup capture gw02-eth0 in container's /tmp/gateway.pcap
INFO:dhcp:DHCP monitor gw02 waiting for replies...
INFO:runner:Test ping gw02->dummy02
INFO:gateway:Gateway gw02 warmup failed at 2019-06-06 20:01:58.372774 with 4
INFO:runner:Test ping gw02->dummy02
INFO:runner:Test ping gw02->dummy02
INFO:runner:Test ping dummy02->gw02
INFO:runner:Test ping dummy02->192.168.84.2
INFO:runner:Test ping gw02->dummy02 from 192.168.84.2
INFO:gateway:Attaching target 2 to gateway group 9a02571e8f02
INFO:config:Loading config from /home/username/daq/local/site/mac_addrs/9a02571e8f02/module_config.json
INFO:host:Device config reloaded: True 9a:02:57:1e:8f:02
INFO:host:Host 2 running with enabled tests ['pass', 'fail', 'ping', 'nmap', 'brute', 'switch', 'macoui', 'bacext', 'tls']
INFO:report:Creating report as inst/reports/report_9a02571e8f02_2019-06-07T030203+0000.md
INFO:report:Skipping missing report header template local/site/report_template.md
INFO:runner:Target port 2 registered 9a:02:57:1e:8f:02
INFO:host:Target port 2 initializing...
INFO:config:Loading config from /home/username/daq/local/site/mac_addrs/9a02571e8f02/module_config.json
INFO:network:Creating mirror pair mirror-2 <-> mirror-2-ext at 1002
INFO:host:Target port 2 startup pcap capture
INFO:network:Directing traffic for 9a:02:57:1e:8f:02 on port 2: True
INFO:topology:Waiting 5s for network to settle
INFO:runner:Port 3 dpid 2 learned 9a:02:57:1e:8f:03
INFO:runner:Gateway for device group 9a02571e8f03 not found, initializing base 3...
INFO:gateway:Initializing gateway 9a02571e8f03 as gw03/30
INFO:gateway:Added networking host gw03 on port 30 at 10.0.0.5
INFO:gateway:Added dummy target dummy03 on port 31 at 10.0.0.6
INFO:gateway:Gateway 3 startup capture gw03-eth0 in container's /tmp/gateway.pcap
INFO:dhcp:DHCP monitor gw03 waiting for replies...
INFO:runner:Test ping gw03->dummy03
INFO:runner:Test ping gw03->dummy03
INFO:runner:Test ping dummy03->gw03
INFO:runner:Test ping dummy03->192.168.84.3
INFO:runner:Test ping gw03->dummy03 from 192.168.84.3
INFO:gateway:Attaching target 3 to gateway group 9a02571e8f03
INFO:config:Loading config from /home/username/daq/local/site/mac_addrs/9a02571e8f03/module_config.json
INFO:host:Device config reloaded: True 9a:02:57:1e:8f:03
INFO:host:Host 3 running with enabled tests ['pass', 'fail', 'ping', 'nmap', 'brute', 'switch', 'macoui', 'bacext', 'tls']
INFO:report:Creating report as inst/reports/report_9a02571e8f03_2019-06-07T030227+0000.md
INFO:report:Skipping missing report header template local/site/report_template.md
INFO:runner:Target port 3 registered 9a:02:57:1e:8f:03
INFO:host:Target port 3 initializing...
INFO:config:Loading config from /home/username/daq/local/site/mac_addrs/9a02571e8f03/module_config.json
INFO:network:Creating mirror pair mirror-3 <-> mirror-3-ext at 1003
INFO:host:Target port 3 startup pcap capture
INFO:network:Directing traffic for 9a:02:57:1e:8f:03 on port 3: True
INFO:topology:Waiting 5s for network to settle
INFO:runner:DHCP notify 9a:02:57:1e:8f:01 is 10.20.12.38 on gw01 (pass/None/54)
INFO:runner:DHCP device 9a:02:57:1e:8f:01 ignoring spurious notify
INFO:runner:DHCP notify 9a:02:57:1e:8f:02 is 10.20.84.39 on gw02 (pass/None/40)
INFO:runner:DHCP device 9a:02:57:1e:8f:02 ignoring spurious notify
INFO:host:Target port 1 waiting for dhcp as 9a:02:57:1e:8f:01
INFO:host:Target port 2 waiting for dhcp as 9a:02:57:1e:8f:02
INFO:host:Target port 3 waiting for dhcp as 9a:02:57:1e:8f:03
INFO:runner:DHCP notify 9a:02:57:1e:8f:03 is 10.20.23.40 on gw03 (pass/None/41)
INFO:gateway:Ready target 9a:02:57:1e:8f:03 from gateway group 9a02571e8f03
INFO:runner:DHCP activating target 9a:02:57:1e:8f:03
INFO:host:Target port 3 triggered as 10.20.23.40
INFO:runner:Test ping gw03->10.20.23.40
INFO:runner:Test ping gw03->10.20.23.40
INFO:runner:Test ping gw03->10.20.23.40 from 192.168.84.3
INFO:host:Target port 3 monitor scan complete
INFO:host:Target port 3 done with base.
INFO:host:Target port 3 background scan for 30s
INFO:runner:DHCP notify 9a:02:57:1e:8f:01 is 10.20.12.38 on gw01 (pass/None/30)
INFO:gateway:Ready target 9a:02:57:1e:8f:01 from gateway group 9a02571e8f01
INFO:runner:DHCP activating target 9a:02:57:1e:8f:01
INFO:host:Target port 1 triggered as 10.20.12.38
INFO:runner:Test ping gw01->10.20.12.38
INFO:runner:Test ping gw01->10.20.12.38
INFO:runner:Test ping gw01->10.20.12.38 from 192.168.84.1
INFO:host:Target port 1 monitor scan complete
INFO:host:Target port 1 done with base.
INFO:host:Target port 1 background scan for 30s
INFO:host:Target port 3 scan complete
INFO:host:Target port 3 monitor scan complete
INFO:config:Writing config to inst/run-port-03/nodes/pass03/tmp/module_config.json
INFO:docker:Target port 3 test pass running
INFO:docker:Target port 3 test pass passed 1.37368s
INFO:host:test_host callback pass/pass03 was 0 with None
INFO:config:Writing config to inst/run-port-03/nodes/fail03/tmp/module_config.json
INFO:docker:Target port 3 test fail running
INFO:runner:DHCP notify 9a:02:57:1e:8f:02 is 10.20.84.39 on gw02 (pass/None/53)
INFO:gateway:Ready target 9a:02:57:1e:8f:02 from gateway group 9a02571e8f02
INFO:runner:DHCP activating target 9a:02:57:1e:8f:02
INFO:host:Target port 2 triggered as 10.20.84.39
INFO:docker:Target port 3 test fail failed 1.758117s: 1 None
INFO:host:test_host callback fail/fail03 was 1 with None
INFO:config:Writing config to inst/run-port-03/nodes/ping03/tmp/module_config.json
INFO:docker:Target port 3 test ping running
INFO:runner:Test ping gw02->10.20.84.39
INFO:runner:Test ping gw02->10.20.84.39
INFO:runner:Test ping gw02->10.20.84.39 from 192.168.84.2
INFO:host:Target port 2 monitor scan complete
INFO:host:Target port 2 done with base.
INFO:host:Target port 2 background scan for 30s
INFO:runner:DHCP notify 9a:02:57:1e:8f:03 is 10.20.23.40 on gw03 (pass/None/42)
INFO:runner:DHCP activation group 9a02571e8f03 already activated
INFO:host:Target port 1 scan complete
INFO:host:Target port 1 monitor scan complete
INFO:config:Writing config to inst/run-port-01/nodes/pass01/tmp/module_config.json
INFO:docker:Target port 1 test pass running
INFO:docker:Target port 3 test ping passed 10.902412s
INFO:host:test_host callback ping/ping03 was 0 with None
INFO:config:Writing config to inst/run-port-03/nodes/nmap03/tmp/module_config.json
INFO:docker:Target port 3 test nmap running
INFO:docker:Target port 1 test pass passed 2.392317s
INFO:host:test_host callback pass/pass01 was 0 with None
INFO:config:Writing config to inst/run-port-01/nodes/fail01/tmp/module_config.json
INFO:docker:Target port 1 test fail running
INFO:docker:Target port 1 test fail failed 1.390234s: 1 None
INFO:host:test_host callback fail/fail01 was 1 with None
INFO:config:Writing config to inst/run-port-01/nodes/ping01/tmp/module_config.json
INFO:docker:Target port 1 test ping running
INFO:runner:DHCP notify 9a:02:57:1e:8f:01 is 10.20.12.38 on gw01 (pass/None/38)
INFO:runner:DHCP activation group 9a02571e8f01 already activated
INFO:docker:Target port 3 test nmap passed 7.438291s
INFO:host:test_host callback nmap/nmap03 was 0 with None
INFO:config:Writing config to inst/run-port-03/nodes/brute03/tmp/module_config.json
INFO:docker:Target port 3 test brute running
INFO:docker:Target port 3 test brute passed 5.28938s
INFO:host:test_host callback brute/brute03 was 0 with None
INFO:config:Writing config to inst/run-port-03/nodes/switch03/tmp/module_config.json
INFO:docker:Target port 3 test switch running
INFO:docker:Target port 1 test ping passed 11.302839s
INFO:host:test_host callback ping/ping01 was 0 with None
INFO:config:Writing config to inst/run-port-01/nodes/nmap01/tmp/module_config.json
INFO:docker:Target port 1 test nmap running
INFO:docker:Target port 3 test switch passed 2.302819s
INFO:host:test_host callback switch/switch03 was 0 with None
INFO:config:Writing config to inst/run-port-03/nodes/macoui03/tmp/module_config.json
INFO:docker:Target port 3 test macoui running
INFO:docker:Target port 3 test macoui passed 1.645939s
INFO:host:test_host callback macoui/macoui03 was 0 with None
INFO:config:Writing config to inst/run-port-03/nodes/bacext03/tmp/module_config.json
INFO:docker:Target port 3 test bacext running
INFO:docker:Target port 1 test nmap passed 7.697249s
INFO:host:test_host callback nmap/nmap01 was 0 with None
INFO:config:Writing config to inst/run-port-01/nodes/brute01/tmp/module_config.json
INFO:docker:Target port 1 test brute running
INFO:host:Target port 2 scan complete
INFO:host:Target port 2 monitor scan complete
INFO:config:Writing config to inst/run-port-02/nodes/pass02/tmp/module_config.json
INFO:docker:Target port 2 test pass running
INFO:docker:Target port 3 test bacext passed 8.492077s
INFO:host:test_host callback bacext/bacext03 was 0 with None
INFO:config:Writing config to inst/run-port-03/nodes/tls03/tmp/module_config.json
INFO:docker:Target port 3 test tls running
INFO:docker:Target port 2 test pass passed 2.688811s
INFO:host:test_host callback pass/pass02 was 0 with None
INFO:config:Writing config to inst/run-port-02/nodes/fail02/tmp/module_config.json
INFO:docker:Target port 2 test fail running
INFO:docker:Target port 3 test tls passed 2.438128s
INFO:host:test_host callback tls/tls03 was 0 with None
INFO:host:Target port 3 no more tests remaining
INFO:report:Finalizing report report_9a02571e8f03_2019-06-07T030227+0000.md
INFO:report:Copying test report inst/run-port-03/nodes/ping03/tmp/report.txt
INFO:report:Copying test report inst/run-port-03/nodes/nmap03/tmp/report.txt
INFO:report:Copying test report inst/run-port-03/nodes/brute03/tmp/report.txt
INFO:report:Copying test report inst/run-port-03/nodes/switch03/tmp/report.txt
INFO:report:Copying test report inst/run-port-03/nodes/macoui03/tmp/report.txt
INFO:report:Copying test report inst/run-port-03/nodes/bacext03/tmp/report.txt
INFO:report:Copying test report inst/run-port-03/nodes/tls03/tmp/report.txt
INFO:report:Copying report to local/site/mac_addrs/9a02571e8f03/device_report.md
INFO:gcp:Ignoring report upload: not configured
INFO:docker:Target port 2 test fail failed 1.6162s: 1 None
INFO:host:test_host callback fail/fail02 was 1 with None
INFO:config:Writing config to inst/run-port-02/nodes/ping02/tmp/module_config.json
INFO:docker:Target port 2 test ping running
INFO:docker:Target port 1 test brute passed 7.818764s
INFO:host:test_host callback brute/brute01 was 0 with None
INFO:config:Writing config to inst/run-port-01/nodes/switch01/tmp/module_config.json
INFO:docker:Target port 1 test switch running
INFO:runner:Target port 3 finalize: [] (target set not active)
INFO:runner:Target port 3 cancel 9a:02:57:1e:8f:03 (#3/0).
INFO:network:Directing traffic for 9a:02:57:1e:8f:03 on port 3: False
INFO:topology:Waiting 5s for network to settle
INFO:host:Target port 3 terminate, trigger False
INFO:network:Deleting mirror pair mirror-3 <-> mirror-3-ext
INFO:gateway:Detach target 3 from gateway group 9a02571e8f03
INFO:runner:Retiring target gateway 3, 9a:02:57:1e:8f:03, 9a02571e8f03, 3
INFO:gateway:Terminating gateway 3/9a02571e8f03
WARNING:runner:Suppressing future tests because test done in single shot.
INFO:runner:Remaining target sets: [1, 2]
INFO:docker:Target port 1 test switch passed 7.473134s
INFO:host:test_host callback switch/switch01 was 0 with None
INFO:config:Writing config to inst/run-port-01/nodes/macoui01/tmp/module_config.json
INFO:docker:Target port 1 test macoui running
INFO:runner:DHCP notify 9a:02:57:1e:8f:02 is 10.20.84.39 on gw02 (pass/None/48)
INFO:runner:DHCP activation group 9a02571e8f02 already activated
INFO:docker:Target port 1 test macoui passed 1.504814s
INFO:host:test_host callback macoui/macoui01 was 0 with None
INFO:config:Writing config to inst/run-port-01/nodes/bacext01/tmp/module_config.json
INFO:docker:Target port 1 test bacext running
INFO:docker:Target port 2 test ping passed 11.636243s
INFO:host:test_host callback ping/ping02 was 0 with None
INFO:config:Writing config to inst/run-port-02/nodes/nmap02/tmp/module_config.json
INFO:docker:Target port 2 test nmap running
INFO:docker:Target port 1 test bacext passed 6.869377s
INFO:host:test_host callback bacext/bacext01 was 0 with None
INFO:config:Writing config to inst/run-port-01/nodes/tls01/tmp/module_config.json
INFO:docker:Target port 1 test tls running
INFO:docker:Target port 1 test tls passed 1.756588s
INFO:host:test_host callback tls/tls01 was 0 with None
INFO:host:Target port 1 no more tests remaining
INFO:report:Finalizing report report_9a02571e8f01_2019-06-07T030147+0000.md
INFO:report:Copying test report inst/run-port-01/nodes/ping01/tmp/report.txt
INFO:report:Copying test report inst/run-port-01/nodes/nmap01/tmp/report.txt
INFO:report:Copying test report inst/run-port-01/nodes/brute01/tmp/report.txt
INFO:report:Copying test report inst/run-port-01/nodes/switch01/tmp/report.txt
INFO:report:Copying test report inst/run-port-01/nodes/macoui01/tmp/report.txt
INFO:report:Copying test report inst/run-port-01/nodes/bacext01/tmp/report.txt
INFO:report:Copying test report inst/run-port-01/nodes/tls01/tmp/report.txt
INFO:report:Copying report to local/site/mac_addrs/9a02571e8f01/device_report.md
INFO:gcp:Ignoring report upload: not configured
INFO:docker:Target port 2 test nmap passed 7.670636s
INFO:host:test_host callback nmap/nmap02 was 0 with None
INFO:config:Writing config to inst/run-port-02/nodes/brute02/tmp/module_config.json
INFO:docker:Target port 2 test brute running
INFO:runner:Target port 1 finalize: [] (target set not active)
INFO:runner:Target port 1 cancel 9a:02:57:1e:8f:01 (#3/0).
INFO:network:Directing traffic for 9a:02:57:1e:8f:01 on port 1: False
INFO:topology:Waiting 5s for network to settle
INFO:host:Target port 1 terminate, trigger False
INFO:network:Deleting mirror pair mirror-1 <-> mirror-1-ext
INFO:gateway:Detach target 1 from gateway group 9a02571e8f01
INFO:runner:Retiring target gateway 1, 9a:02:57:1e:8f:01, 9a02571e8f01, 1
INFO:gateway:Terminating gateway 1/9a02571e8f01
INFO:runner:Remaining target sets: [2]
INFO:docker:Target port 2 test brute passed 7.239186s
INFO:host:test_host callback brute/brute02 was 0 with None
INFO:config:Writing config to inst/run-port-02/nodes/switch02/tmp/module_config.json
INFO:docker:Target port 2 test switch running
INFO:docker:Target port 2 test switch passed 1.310238s
INFO:host:test_host callback switch/switch02 was 0 with None
INFO:config:Writing config to inst/run-port-02/nodes/macoui02/tmp/module_config.json
INFO:docker:Target port 2 test macoui running
INFO:docker:Target port 2 test macoui passed 1.590778s
INFO:host:test_host callback macoui/macoui02 was 0 with None
INFO:config:Writing config to inst/run-port-02/nodes/bacext02/tmp/module_config.json
INFO:docker:Target port 2 test bacext running
INFO:docker:Target port 2 test bacext passed 6.585959s
INFO:host:test_host callback bacext/bacext02 was 0 with None
INFO:config:Writing config to inst/run-port-02/nodes/tls02/tmp/module_config.json
INFO:docker:Target port 2 test tls running
INFO:docker:Target port 2 test tls passed 1.642623s
INFO:host:test_host callback tls/tls02 was 0 with None
INFO:host:Target port 2 no more tests remaining
INFO:report:Finalizing report report_9a02571e8f02_2019-06-07T030203+0000.md
INFO:report:Copying test report inst/run-port-02/nodes/ping02/tmp/report.txt
INFO:report:Copying test report inst/run-port-02/nodes/nmap02/tmp/report.txt
INFO:report:Copying test report inst/run-port-02/nodes/brute02/tmp/report.txt
INFO:report:Copying test report inst/run-port-02/nodes/switch02/tmp/report.txt
INFO:report:Copying test report inst/run-port-02/nodes/macoui02/tmp/report.txt
INFO:report:Copying test report inst/run-port-02/nodes/bacext02/tmp/report.txt
INFO:report:Copying test report inst/run-port-02/nodes/tls02/tmp/report.txt
INFO:report:Copying report to local/site/mac_addrs/9a02571e8f02/device_report.md
INFO:gcp:Ignoring report upload: not configured
INFO:runner:Target port 2 finalize: [] (target set not active)
INFO:runner:Target port 2 cancel 9a:02:57:1e:8f:02 (#3/0).
INFO:network:Directing traffic for 9a:02:57:1e:8f:02 on port 2: False
INFO:topology:Waiting 5s for network to settle
INFO:host:Target port 2 terminate, trigger False
INFO:network:Deleting mirror pair mirror-2 <-> mirror-2-ext
INFO:gateway:Detach target 2 from gateway group 9a02571e8f02
INFO:runner:Retiring target gateway 2, 9a:02:57:1e:8f:02, 9a02571e8f02, 2
INFO:gateway:Terminating gateway 2/9a02571e8f02
INFO:runner:Remaining target sets: []
WARNING:runner:No active ports remaining (0 monitors), ending test run.
INFO:runner:Stopping network...
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
INFO:runner:Done with runner.
INFO:daq:DAQ runner returned 0
Cleanup docker kill daq-faux-1
daq-faux-1
Cleanup docker kill daq-faux-2
daq-faux-2
Cleanup docker kill daq-faux-3
daq-faux-3
Done with run, exit 0
</pre>
