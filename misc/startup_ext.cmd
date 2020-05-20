autostart bin/external_ovs
autostart cmd/faux
autostart bin/bridge_link ext-ovs faux 2
autostart bin/bridge_link ext-ovs ext-ovs-sec 7
