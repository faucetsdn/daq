# Building DAQ

You shouldn't need to do this unless you're doing active development on DAQ itself. Doing this
will require installing more prerequisites that aren't indicated above. See
<code>bin/setup_base</code> or <code>docker/Docker.base</code> for details.

To build containers for basic execution, which can take a long time:

<pre>
  $ <b>cmd/build</b>
</pre>

To run the development version, use the simple executor-run command:

<pre>
  $ <b>cmd/exrun</b>
</pre>

Build the runner container, which can take a <em>really</em> long time:

<pre>
  $ <b>cmd/inbuild</b>
</pre>

You can also clean all the stuffs:

<pre>
  $ <b>cmd/clean</b>
</pre>

...which is sometimes necessary to gaurintee a clean build.
Be warned, it also might clean some other images/containers from other projects.

