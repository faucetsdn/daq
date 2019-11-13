To get up and going with the DAQ basics, all you need to do is...

(starting with a vanilla Debian Linux install)
<pre>
# git clone http://github.com/faucetsdn/daq.git
&hellip;
# cd daq
# bin/setup_daq
&hellip;
Docker execution failed, is the docker group setup?
If this is the first time, try logging out and log back in again.
</pre>
Be a good person and logout then log back in again... and then...
<pre>
# cd daq
# bin/setup_daq
&hellip;
Done with setup_daq.
# cmd/run -s
&hellip;
Done with run, exit 0
</pre>

Then declare victory.
