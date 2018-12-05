"""Faucet-specific topology module"""

import logging
import os
import yaml

from gateway import Gateway

LOGGER = logging.getLogger('topology')

class FaucetTopology():
    """Topology manager specific to FAUCET configs"""

    OUTPUT_NETWORK_FILE = "inst/faucet.yaml"
    MAC_PLACEHOLDER = "@mac:"
    DNS_PLACEHOLDER = "@dns:"
    CONT_PLACEHOLDER = "@ctrl:"
    INST_FILE_PREFIX = "inst/"
    BROADCAST_MAC = "ff:ff:ff:ff:ff:ff"
    PORT_ACL_NAME_FORMAT = "dp_%s_port_%d_acl"
    DP_ACL_FILE_FORMAT = "dp_port_acls.yaml"
    PORT_ACL_FILE_FORMAT = "port_acls/dp_%s_port_%d_acl.yaml"
    TEMPLATE_FILE_FORMAT = "inst/acl_templates/template_%s_acl.yaml"
    FROM_ACL_KEY_FORMAT = "@from:template_%s_acl"
    INCOMING_ACL_FORMAT = "dp_%s_incoming_acl"
    PORTSET_ACL_FORMAT = "dp_%s_portset_acl"
    MIRROR_PORT_BASE = 1000
    PRI_STACK_PORT = 1
    DEFAULT_VLAN = 10

    def __init__(self, config, pri):
        self._mac_map = {}
        self.config = config
        self.pri = pri
        self.pri_name = pri.name
        self.sec_port = int(config.get('sec_port', "7"), 0)
        self.sec_name = 'sec'
        self.sec_dpid = int(config.get('ext_dpid', "2"), 0)
        self._device_specs = self._load_device_specs()
        self.topology = self._make_base_network_topology()

    def initialize(self):
        """Initialize this topology"""
        LOGGER.debug("Converting existing network topology...")
        self._write_network_topology()
        self.generate_acls()

    def start(self):
        """Start this instance"""
        LOGGER.info("Starting faucet...")
        output = self.pri.cmd('cmd/faucet && echo SUCCESS')
        if not output.strip().endswith('SUCCESS'):
            LOGGER.info('Faucet output: %s', output)
            assert False, 'Faucet startup failed'

    def stop(self):
        """Stop this instance"""
        LOGGER.debug("Stopping faucet...")
        self.pri.cmd('docker kill daq-faucet')

    def _load_file(self, filename):
        if not os.path.isfile(filename):
            raise Exception("File %s does not exist." % filename)
        LOGGER.debug("Loading file %s", filename)
        with open(filename) as stream:
            return yaml.safe_load(stream)

    def get_ext_intf(self):
        """Return the external interface for seconday, if any"""
        return self.config.get('ext_intf')

    def get_sec_dpid(self):
        """Return the secondary dpid"""
        return self.sec_dpid

    def get_sec_port(self):
        """Return the secondary stacking port"""
        return self.sec_port

    def get_device_intfs(self):
        """Return list of secondary device interfaces"""
        intf_split = self.config.get('intf_names', "").split(",")
        intf_names = intf_split if intf_split[0] else []
        device_intfs = []
        for port in range(1, self.sec_port):
            named_port = port <= len(intf_names)
            default_name = '%s-%s' % (self.sec_name, port)
            device_intfs.append(intf_names[port-1] if named_port else default_name)
        return device_intfs

    def direct_port_traffic(self, target_mac, port_no, target):
        """Direct traffic from a given mac to specified port set"""
        if target is None and target_mac in self._mac_map:
            del self._mac_map[target_mac]
        elif target is not None and target_mac not in self._mac_map:
            self._mac_map[target_mac] = target
        else:
            LOGGER.debug('Ignoring no-change in port status for %s on %d', target_mac, port_no)
            return
        self.generate_acls(port=port_no)

    def _ensure_entry(self, root, key, value):
        if key not in root:
            root[key] = value
        return root[key]

    def _load_device_specs(self):
        device_specs = self.config.get('device_specs')
        if device_specs:
            LOGGER.info('Loading device specs from %s', device_specs)
            return self._load_file(device_specs)
        LOGGER.info('No device_specs file specified, skipping...')
        return None

    def _make_mirror_interface(self, input_port):
        interface = {}
        interface['name'] = 'mirror-%02d' % input_port
        interface['output_only'] = True
        return interface

    def _make_gw_interface(self, input_port):
        input_port = input_port
        interface = {}
        interface['acl_in'] = self.PORTSET_ACL_FORMAT % self.pri_name
        interface['native_vlan'] = self.DEFAULT_VLAN
        return interface

    def _make_pri_stack_interface(self):
        interface = {}
        interface['acl_in'] = self.INCOMING_ACL_FORMAT % self.pri_name
        interface['stack'] = {'dp': self.sec_name, 'port': self.sec_port}
        interface['name'] = 'stack_pri'
        return interface

    def _make_sec_stack_interface(self):
        interface = {}
        interface['acl_in'] = self.INCOMING_ACL_FORMAT % self.sec_name
        interface['stack'] = {'dp': self.pri_name, 'port': self.PRI_STACK_PORT}
        interface['name'] = self.config.get('ext_intf', 'stack_sec')
        return interface

    def _make_default_acl_rules(self):
        rules = []
        if not self._append_acl_template(rules, 'raw'):
            rules.append(self._augment_sec_port_acl(self._make_default_allow_rule()))
        return rules

    def _make_default_acls(self):
        acls = {}
        for port in range(1, self.sec_port):
            acl_name = self.PORT_ACL_NAME_FORMAT % (self.sec_name, port)
            acls[acl_name] = self._make_default_acl_rules()
        return acls

    def _make_sec_port_interface(self, port):
        interface = {}
        interface['acl_in'] = self.PORT_ACL_NAME_FORMAT % (self.sec_name, port)
        interface['native_vlan'] = self.DEFAULT_VLAN
        return interface

    def _make_pri_interfaces(self):
        interfaces = {}
        interfaces[self.PRI_STACK_PORT] = self._make_pri_stack_interface()
        for port in self._get_gw_ports():
            interfaces[port] = self._make_gw_interface(port)
        for input_port in range(1, self.sec_port):
            mirror_port = self.MIRROR_PORT_BASE + input_port
            interfaces[mirror_port] = self._make_mirror_interface(input_port)
        return interfaces

    def _make_sec_interfaces(self):
        interfaces = {}
        interfaces[self.sec_port] = self._make_sec_stack_interface()
        for port in range(1, self.sec_port):
            interfaces[port] = self._make_sec_port_interface(port)
        return interfaces

    def _make_acl_include(self):
        return [self.DP_ACL_FILE_FORMAT]

    def _make_acl_include_optional(self):
        include_optional = []
        for port in range(1, self.sec_port):
            include_optional += [self.PORT_ACL_FILE_FORMAT % (self.sec_name, port)]
        return include_optional

    def _make_pri_topology(self):
        pri_dp = {}
        pri_dp['dp_id'] = 1
        pri_dp['name'] = self.pri_name
        pri_dp['stack'] = {'priority':1}
        pri_dp['interfaces'] = self._make_pri_interfaces()
        return pri_dp

    def _make_sec_topology(self):
        sec_dp = {}
        sec_dp['dp_id'] = self.sec_dpid
        sec_dp['name'] = self.sec_name
        sec_dp['interfaces'] = self._make_sec_interfaces()
        return sec_dp

    def _make_base_network_topology(self):
        dps = {}
        dps['pri'] = self._make_pri_topology()
        dps['sec'] = self._make_sec_topology()
        topology = {}
        topology['dps'] = dps
        topology['acls'] = self._make_default_acls()
        topology['vlans'] = {10:{'description': "Internal DAQ vlan"}}
        topology['include'] = self._make_acl_include()
        topology['include-optional'] = self._make_acl_include_optional()
        return topology

    def _write_network_topology(self):
        LOGGER.info('Writing network config to %s', self.OUTPUT_NETWORK_FILE)
        with open(self.OUTPUT_NETWORK_FILE, "w") as output_stream:
            yaml.safe_dump(self.topology, stream=output_stream)

    def generate_acls(self, port=None):
        """Generate all ACLs required for dynamic system operation"""
        self._generate_main_acls()
        if not self._generate_port_acls(port=port):
            LOGGER.info('Cleared port acls for port %s', port)

    def _get_gw_ports(self):
        min_port = Gateway.SET_SPACING
        max_port = Gateway.SET_SPACING * self.sec_port
        return list(range(min_port, max_port))

    def _get_bcast_ports(self):
        return [1] + self._get_gw_ports()

    def _generate_main_acls(self):
        incoming_acl = []
        portset_acl = []
        secondary_acl = []

        for target_mac in self._mac_map:
            target = self._mac_map[target_mac]
            mirror_port = self.MIRROR_PORT_BASE + target['port']
            incoming = list(range(target['range'][0], target['range'][1])) + [mirror_port]
            self._add_acl_rule(incoming_acl, dl_src=target_mac,
                               in_vlan=self.DEFAULT_VLAN, ports=incoming)
            self._add_acl_rule(incoming_acl, dl_src=target_mac, port=mirror_port)
            portset = [1, mirror_port]
            self._add_acl_rule(portset_acl, dl_dst=target_mac, ports=portset)

        self._add_acl_rule(incoming_acl, allow=0)
        self._add_acl_rule(portset_acl, dl_dst=self.BROADCAST_MAC,
                           ports=self._get_bcast_ports(), allow=1)
        self._add_acl_rule(portset_acl, allow=1)
        self._add_acl_rule(secondary_acl, allow=1, out_vlan=self.DEFAULT_VLAN)

        acls = {}
        acls[self.INCOMING_ACL_FORMAT % self.pri_name] = incoming_acl
        acls[self.PORTSET_ACL_FORMAT % self.pri_name] = portset_acl
        acls[self.INCOMING_ACL_FORMAT % self.sec_name] = secondary_acl

        pri_acls = {}
        pri_acls["acls"] = acls

        filename = self.INST_FILE_PREFIX + self.DP_ACL_FILE_FORMAT
        LOGGER.debug("Writing updated pri acls to %s", filename)
        with open(filename, "w") as output_stream:
            yaml.safe_dump(pri_acls, stream=output_stream)

    def _maybe_apply(self, target, keyword, origin, source=None):
        source_keyword = source if source else keyword
        if source_keyword in origin:
            target[keyword] = origin[source_keyword]

    def _add_acl_rule(self, acl, **kwargs):
        in_vlan = {}
        if 'in_vlan' in kwargs:
            in_vlan['pop_vlans'] = True
            in_vlan['vlan_vid'] = kwargs['in_vlan']

        output = {}
        self._maybe_apply(output, 'port', kwargs)
        self._maybe_apply(output, 'ports', kwargs)
        self._maybe_apply(output, 'vlan_vid', kwargs, 'out_vlan')
        self._maybe_apply(output, 'pop_vlans', in_vlan)

        actions = {}
        if output:
            actions['output'] = output
        self._maybe_apply(actions, 'allow', kwargs)
        self._maybe_apply(actions, 'mirror', kwargs)

        subrule = {}
        subrule["actions"] = actions
        self._maybe_apply(subrule, "dl_src", kwargs)
        self._maybe_apply(subrule, "dl_dst", kwargs)
        self._maybe_apply(subrule, "vlan_vid", in_vlan)

        rule = {}
        rule["rule"] = subrule

        acl.append(rule)

    def _generate_port_acls(self, port=None):
        if port:
            return self._generate_port_acl(port=port)
        for range_port in range(1, self.sec_port):
            self._generate_port_acl(port=range_port)
        return True

    def _generate_port_acl(self, port=None):
        target_mac = None
        rules = []
        if self._device_specs:
            for check_mac in self._mac_map:
                if self._mac_map[check_mac]['port'] == port:
                    target_mac = check_mac
                    self._add_acl_port_rules(rules, target_mac, port)

        filename = self.INST_FILE_PREFIX + self.PORT_ACL_FILE_FORMAT % (self.sec_name, port)
        if target_mac:
            assert self._append_acl_template(rules, 'baseline'), 'Missing ACL template baseline'
            self._append_device_default_allow(rules, target_mac)
            self._write_port_acl(port, rules, filename)
        elif os.path.isfile(filename):
            LOGGER.debug("Removing unused port acl file %s", filename)
            os.remove(filename)
        return target_mac

    def _write_port_acl(self, port, rules, filename):
        LOGGER.debug("Writing port acl file %s", filename)
        acl_name = self.PORT_ACL_NAME_FORMAT % (self.sec_name, port)
        acls = {}
        acls[acl_name] = rules
        port_acl = {}
        port_acl['acls'] = acls
        with open(filename, "w") as output_stream:
            yaml.safe_dump(port_acl, stream=output_stream)

    def _add_acl_port_rules(self, rules, target_mac, port):
        mac_map = self._device_specs['macAddrs']
        if target_mac not in mac_map:
            LOGGER.info("No device spec found for %s", target_mac)
            device_type = 'default'
        else:
            device_info = mac_map[target_mac]
            device_type = device_info['type'] if 'type' in device_info else 'default'
        LOGGER.info("Applying acl template %s/%s to port %s", target_mac, device_type, port)
        self._append_acl_template(rules, device_type, target_mac)

    def _sanitize_mac(self, mac_addr):
        return mac_addr.replace(':', '')

    def device_group_for(self, target_mac):
        """Find the target device group for the given address"""
        if not self._device_specs:
            return self._sanitize_mac(target_mac)
        mac_map = self._device_specs['macAddrs']
        if target_mac in mac_map and 'group' in mac_map[target_mac]:
            return mac_map[target_mac]['group']
        return self._sanitize_mac(target_mac)

    def _make_default_allow_rule(self):
        actions = {'allow': 1}
        subrule = {'actions': actions}
        return {'rule': subrule}

    def _augment_sec_port_acl(self, acls):
        actions = acls['rule']['actions']
        assert not 'output' in actions, 'output actions explicitly defined'
        if actions['allow']:
            actions['output'] = {'port': self.sec_port}
        return acls

    def _append_device_default_allow(self, rules, target_mac):
        device_spec = self._device_specs['macAddrs'].get(target_mac)
        if device_spec and 'default_allow' in device_spec:
            allow_action = 1 if device_spec['default_allow'] else 0
            actions = {'allow': allow_action}
            subrule = {'actions': actions}
            subrule['description'] = "device_spec default_allow"
            acl = {'rule': subrule}
            rules.append(self._augment_sec_port_acl(acl))

    def _append_acl_template(self, rules, template, target_mac=None):
        filename = self.TEMPLATE_FILE_FORMAT % template
        if not self._device_specs:
            return False
        template_acl = self._load_file(filename)
        template_key = self.FROM_ACL_KEY_FORMAT % template
        for acl in template_acl['acls'][template_key]:
            new_rule = acl['rule']
            self._resolve_template_field(new_rule, 'dl_src', target_mac=target_mac)
            self._resolve_template_field(new_rule, 'nw_dst')
            rules.append(self._augment_sec_port_acl(acl))
        return True

    def _resolve_template_field(self, rule, field, target_mac=None):
        if field not in rule:
            return
        placeholder = rule[field]
        if placeholder.startswith(self.MAC_PLACEHOLDER):
            rule[field] = target_mac
        elif placeholder.startswith(self.DNS_PLACEHOLDER):
            del rule[field]
        elif placeholder.startswith(self.CONT_PLACEHOLDER):
            del rule[field]
