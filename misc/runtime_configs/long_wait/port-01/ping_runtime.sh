# Sleep for 5 minutes to let long-lease dhcp discovery happen.
sleep_time=$((5*60))
echo Sleeping for ${sleep_time}s to wait for DHCP.
sleep $sleep_time
