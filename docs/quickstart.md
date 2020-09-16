To get up and going with the DAQ basics, all you need to do is...

## Install
(starting with a vanilla Debian Linux install)
<pre>
$ git clone http://github.com/faucetsdn/daq.git
&hellip;
$ cd daq
$ bin/setup_daq
&hellip;
Docker execution failed, is the docker group setup?
If this is the first time, try logging out and log back in again.
</pre>
Be a good person and logout then log back in again... and then...

## Build Required Docker Images
<pre>
$ cd daq
$ cmd/build
</pre>

## (Optional) Physical Switch Setup
### AT x230 series with factory setting
1. Plug one ethernet cable into the last port of the switch.
2. If the switch has more than 8 ethernet ports, change **interface port1.0.1-1.0.7** in  **etc/switch_configs/at_8ports.cfg** to **interface port1.0.1-1.0.(number of ports - 1)**. Everything else can stay the same.
3. Find interface name that's connected to switch e.g. enx00e04c68036b
4. run <pre>$ sudo bin/setup_switch enx00e04c68036b </pre> replace enx00e04c68036b with your interface name. After about 2 mins, the switch is ready to be used by DAQ.
5. Confirm you can ping switch at 192.168.1.1
6. Connect another ethernet cable into second to last port of the switch and find the interface name. 
7. Create **local/system.conf** to specify switch configurations and fill in the following information: 
  <pre>
  #Load the defaults
  source config/system/default.yaml
  ext_dpid=0x12345
  ext_ctrl=enx00e04c68036b <-- replace with first interface name
  ext_intf=enx00e03c689934 <-- replace with second interface name
  ext_ofpt=6653
  ext_ofip=192.168.1.10/16
  ext_addr=192.168.1.1</pre>
 8. Verify switch config with 
 <pre>$ bin/physical_sec </pre>
 9. Plug in a test device in any port not in use.
See [test_lab](test_lab.md) for details and additional troubleshooting.

## Test Run
<pre>
$ cmd/run -s
&hellip;
Done with run, exit 0
</pre>
Reports generated fall under **inst/reports**. An example report can be viewed [here.](report.md)

***The system can be further configured by using a [variety of run options](options.md)***

Then declare victory.
