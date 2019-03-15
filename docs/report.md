# Example Device Test Report

<pre>
~/daq$ <b>cat inst/reports/report_9a02571e8f00_2019-03-15T042113+0000.txt</b>
DAQ scan report for device 9a02571e8f00
Started 2019-03-15 04:21:13+00:00

=============== Report summary

skip base.switch.ping
pass base.target.ping target
pass security.ports.nmap

=============== Module ping

Baseline ping test report
# 53 packets captured.
RESULT skip base.switch.ping
RESULT pass base.target.ping target # 10.20.19.37

=============== Module nmap

No open ports found.
RESULT pass security.ports.nmap

=============== Module brute

Target port 10000 not open.

=============== Module switch

LOCAL_IP not configured, assuming no network switch.

=============== Report complete

</pre>
