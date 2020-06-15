filter="ether host 9a:02:57:1e:8f:03 and port 47808"
count=$(tcpdump -en -r /scans/monitor.pcap $filter | wc -l)
echo Found $count from $filter
[ $count -gt 0 ]
