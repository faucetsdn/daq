# Building DAQ

Building DAQ is only required if you are doing active development on DAQ itself (or using head-of
branch features); it will require installing more prerequisites that aren't indicated above.
In addition to some standard packages, it requires specific versions of <code>mininet</code>
and <code>FAUCET</code> that are tied to this specific build (but, you will have to manually
update them in the future).

<code>$ <b>bin/setup_dev</b></code> # Setup of basic dev environment dependencies.

<code>$ <b>cmd/build</b></code> # Build internal docker images.

<code>$ <b>cmd/exrun</b></code> # Run development version rather than <code>cmd/run</code>

<code>$ <b>cmd/clean</b></code> # Clean up basic docker images.

<code>$ <b>bin/clean_dev</b></code> # Clean up development installs.

Sadly, there's no "easy" way to know when you need to run what when, since they simply address
different dependencies.
