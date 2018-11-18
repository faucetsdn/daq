## Testing BACnet

* Setup system like `misc/system_multi.conf`
* Run in no-test mode with bacnet device enabled: `sudo DAQ_FAUX_OPTS=bacnet cmd/run -n`
* Wait until faux-3 gets an IP address:<pre>
&hellip;
INFO:runner:DHCP notify 9a:02:57:1e:8f:03 is 10.20.83.164 on gw02 (None)
&hellip;
</pre>

* Check that bacnet client is running (requires IP address):<pre>
~/daq$ docker exec -ti daq-faux-3 ps ax -H
   PID TTY      STAT   TIME COMMAND
   226 pts/0    Rs+    0:00 ps ax -H
     1 ?        Ss     0:00 /bin/bash bin/start_faux bacnet
   177 ?        Ss     0:00   dhclient
   183 ?        Sl     0:00   java -cp bacnet4j/bacnet4j-1.0-SNAPSHOT-all.jar co
   184 ?        S      0:00   tail -f /dev/null
</pre>

* Run BACnet discovery in the other container:<pre>
~/daq$ docker exec -ti daq-faux-2 bin/bacnet_discover
Scanning bacnet 10.255.255.255 from 10.20.83.163
Binding to address 0.0.0.0:47808
Local address is 10.20.83.163:47808
Using broadcast address 10.255.255.255:47808
Sending whois...
Waiting...
IAm receivedRemoteDevice(instanceNumber=565, address=Address [networkNumber=0, macAddress=[a,14,53,a4,ba,c0]], linkServiceAddress=null)
Processing...
Query remote device RemoteDevice(instanceNumber=565, address=Address [networkNumber=0, macAddress=[a,14,53,a4,ba,c0]], linkServiceAddress=null)
  Multi-state Output 0/Object name = Vegetable
  Multi-state Output 0/State text = [Tomato, Potato, Onion, Broccoli]
  Binary Input 1/Present value = 0
&hellip;
  Multi-state Output 0/Present value = 2
  Device 565/Object name = BACnet device
Done with receive loop
  Device 565/Object name = BACnet device
</pre>

* Also can monitor BACnet traffic exchange (in another window when running discovery):<pre>
~/daq$ sudo tcpdump -eni pri-eth1 port 47808
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on pri-eth1, link-type EN10MB (Ethernet), capture size 262144 bytes
20:32:19.258922 9a:02:57:1e:8f:02 > ff:ff:ff:ff:ff:ff, ethertype IPv4 (0x0800), length 63: 10.20.83.163.47808 > 10.255.255.255.47808: UDP, length 21
20:32:19.258925 9a:02:57:1e:8f:02 > ff:ff:ff:ff:ff:ff, ethertype 802.1Q (0x8100), length 67: vlan 10, p 0, ethertype IPv4, 10.20.83.163.47808 > 10.255.255.255.47808: UDP, length 21
&hellip;
20:32:24.374676 9a:02:57:1e:8f:02 > 9a:02:57:1e:8f:03, ethertype IPv4 (0x0800), length 68: 10.20.83.163.47808 > 10.20.83.164.47808: UDP, length 26
20:32:24.374989 9a:02:57:1e:8f:03 > 9a:02:57:1e:8f:02, ethertype IPv4 (0x0800), length 104: 10.20.83.164.47808 > 10.20.83.163.47808: UDP, length 62
20:32:24.375812 9a:02:57:1e:8f:02 > 9a:02:57:1e:8f:03, ethertype IPv4 (0x0800), length 152: 10.20.83.163.47808 > 10.20.83.164.47808: UDP, length 110
20:32:24.377085 9a:02:57:1e:8f:03 > 9a:02:57:1e:8f:02, ethertype IPv4 (0x0800), length 386: 10.20.83.164.47808 > 10.20.83.163.47808: UDP, length 344
</pre>
