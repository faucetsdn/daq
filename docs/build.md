# Building DAQ

You shouldn't need to do this unless you're doing active development on DAQ itself. Doing this
will require installing more prerequisites that aren't indicated above. See
<code>bin/setup_dev</code> or <code>docker/Docker.base</code> for details on what is installed.
In addition to standard packages, this will also install specific versions of <code>mininet</code>
and <code>FAUCET</code> that are "tied" to this specific build (but, you will have to manually
update them in the fugure).

To build containers for basic execution, which can take a long time:

<pre>
  $ <b>cmd/build</b>
</pre>

To run the development version, use the simple executor-run command:

<pre>
  $ <b>cmd/exrun</b>
</pre>

If needed, build the runner container, which can take a <em>really</em> long time:

<pre>
  $ <b>cmd/inbuild</b>
</pre>

You can also clean all the stuffs:

<pre>
  $ <b>cmd/clean</b>
</pre>

...which is sometimes necessary to gaurintee a clean build.
Be warned, it also might clean some other images/containers from other projects.
