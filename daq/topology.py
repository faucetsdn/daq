"""Faucet-specific topology module"""

import copy
import os
import time
import yaml

from gateway import Gateway

import logger

LOGGER = logger.get_logger('topology')

class FaucetTopology:
    """Topology manager specific to FAUCET configs"""

    MAC_PREFIX = "@mac:"
    DNS_PREFIX = "@dns:"
    CTL_PREFIX = "@ctrl:"
    INST_FILE_PREFIX = "inst/"
    BROADCAST_MAC = "ff:ff:ff:ff:ff:ff"
    IPV4_DL_TYPE = "0x0800"
    ARP_DL_TYPE = "0x0806"
    LLDP_DL_TYPE = "0x88cc"
    PORT_ACL_NAME_FORMAT = "dp_%s_port_%d_acl"
    DP_ACL_FILE_FORMAT = "dp_port_acls.yaml"
    PORT_ACL_FILE_FORMAT = "port_acls/dp_%s_port_%d_acl.yaml"
    TEMPLATE_FILE_FORMAT = INST_FILE_PREFIX + "acl_templates/template_%s_acl.yaml"
    FROM_ACL_KEY_FORMAT = "@from:template_%s_acl"
    TO_ACL_KEY_FORMAT = "@to:template_%s_acl"
    INCOMING_ACL_FORMAT = "dp_%s_incoming_acl"
    PORTSET_ACL_FORMAT = "dp_%s_portset_%d_acl"
    LOCAL_ACL_FORMAT = "dp_%s_local_acl"
    _DEFAULT_SEC_TRUNK_NAME = "trunk_sec"
    _MIRROR_IFACE_FORMAT = "mirror-%d"
    _MIRROR_PORT_BASE = 1000
    _SWITCH_LOCAL_PORT = _MIRROR_PORT_BASE
    _VLAN_BASE = 1000
    PRI_DPID = 1
    PRI_TRUNK_PORT = 1
    PRI_TRUNK_NAME = 'trunk_pri'
    _NO_VLAN = "0x0000/0x1000"

    def __init__(self, config):
        self.config = config
        self.pri = None
        self.pri_name = None
        self.sec_name = 'sec'
        switch_setup = self.config.get('switch_setup', {})
        self.sec_port = int(switch_setup['uplink_port'])
        self.sec_dpid = int(switch_setup['of_dpid'], 0)
        self.ext_ofip = switch_setup.get('lo_addr')
        self.ext_intf = switch_setup.get('data_intf')
        self._settle_sec = int(config['settle_sec'])
        self._device_specs = self._load_device_specs()
        self._port_targets = {}
        self.topology = None

    def initialize(self, pri):
        """Initialize this topology"""
        LOGGER.debug("Converting existing network topology...")
        self.pri = pri
        self.pri_name = pri.name
        self.topology = self._make_base_network_topology()
        self._generate_acls()

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
        return self.ext_intf

    def get_sec_dpid(self):
        """Return the secondary dpid"""
        return self.sec_dpid

    def get_sec_port(self):
        """Return the secondary trunk port"""
        return self.sec_port

    def get_device_intfs(self):
        """Return list of secondary device interfaces"""
        intf_names = list(self.config.get('interfaces', {}).keys())
        device_intfs = []
        for port in range(1, self.sec_port):
            named_port = port <= len(intf_names)
            default_name = '%s-%s' % (self.sec_name, port)
            device_intfs.append(intf_names[port-1] if named_port else default_name)
        return device_intfs

    def direct_port_traffic(self, target_mac, port_no, target):
        """Direct traffic from a port to specified port set"""
        if target is None and port_no in self._port_targets:
            del self._port_targets[port_no]
        elif target is not None and port_no not in self._port_targets:
            self._port_targets[port_no] = target
        else:
            assert self._port_targets[port_no] == target
            LOGGER.debug('Ignoring no-change in port status for %s', port_no)
            return
        self._generate_acls()
        port_set = target['port_set'] if target else None
        self._update_port_vlan(port_no, port_set)
        if self._settle_sec:
            LOGGER.info('Waiting %ds for network to settle', self._settle_sec)
            time.sleep(self._settle_sec)

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

    def mirror_iface_name(self, input_port):
        """Interface name to use for a given mirror port"""
        return self._MIRROR_IFACE_FORMAT % input_port

    def mirror_port(self, input_port):
        """Network port to use for mirroring interface"""
        return self._MIRROR_PORT_BASE + input_port

    def switch_port(self):
        """Network port to use for local switch connection"""
        return self._SWITCH_LOCAL_PORT

    def _make_mirror_interface(self, input_port):
        interface = {}
        interface['name'] = self.mirror_iface_name(input_port)
        interface['output_only'] = True
        return interface

    def _make_switch_interface(self):
        interface = {}
        interface['name'] = 'local_switch'
        interface['native_vlan'] = self._VLAN_BASE
        interface['acl_in'] = self.LOCAL_ACL_FORMAT % (self.pri_name)
        return interface

    def _make_gw_interface(self, port_set):
        interface = {}
        interface['acl_in'] = self.PORTSET_ACL_FORMAT % (self.pri_name, port_set)
        interface['native_vlan'] = self._port_set_vlan(port_set)
        return interface

    def _update_port_vlan(self, port_no, port_set):
        interface = self.topology['dps'][self.sec_name]['interfaces'][port_no]
        interface['native_vlan'] = self._port_set_vlan(port_set)

    def _port_set_vlan(self, port_set=None):
        return self._VLAN_BASE + (port_set if port_set else 0)

    def _make_pri_trunk_interface(self):
        interface = {}
        interface['acl_in'] = self.INCOMING_ACL_FORMAT % self.pri_name
        interface['tagged_vlans'] = self._vlan_tags()
        interface['name'] = self.PRI_TRUNK_NAME
        return interface

    def _make_sec_trunk_interface(self):
        interface = {}
        interface['acl_in'] = self.INCOMING_ACL_FORMAT % self.sec_name
        interface['tagged_vlans'] = self._vlan_tags()
        interface['name'] = self.get_ext_intf() or self._DEFAULT_SEC_TRUNK_NAME
        return interface

    def _vlan_tags(self):
        return list(range(self._VLAN_BASE, self._VLAN_BASE + self.sec_port))

    def _make_default_acl_rules(self):
        rules = []
        if not self._append_acl_template(rules, 'raw'):
            self._append_augmented_rule(rules, self._make_default_allow_rule())
        return rules

    def _make_sec_port_interface(self, port_no):
        interface = {}
        interface['acl_in'] = self.PORT_ACL_NAME_FORMAT % (self.sec_name, port_no)
        interface['native_vlan'] = self._port_set_vlan()
        return interface

    def _make_pri_interfaces(self):
        interfaces = {}
        interfaces[self.PRI_TRUNK_PORT] = self._make_pri_trunk_interface()
        for port_set in range(1, self.sec_port):
            for port in self._get_gw_ports(port_set):
                interfaces[port] = self._make_gw_interface(port_set)
            mirror_port = self.mirror_port(port_set)
            interfaces[mirror_port] = self._make_mirror_interface(port_set)
        interfaces[self._SWITCH_LOCAL_PORT] = self._make_switch_interface()
        return interfaces

    def _make_sec_interfaces(self):
        interfaces = {}
        interfaces[self.sec_port] = self._make_sec_trunk_interface()
        for port in range(1, self.sec_port):
            interfaces[port] = self._make_sec_port_interface(port)
        return interfaces

    def _make_acl_include(self):
        includes = [self.DP_ACL_FILE_FORMAT]
        for port in range(1, self.sec_port):
            base_name = self.PORT_ACL_FILE_FORMAT % (self.sec_name, port)
            includes += [base_name]
        return includes

    def _make_pri_topology(self):
        pri_dp = {}
        pri_dp['dp_id'] = self.PRI_DPID
        pri_dp['interfaces'] = self._make_pri_interfaces()
        return pri_dp

    def _make_sec_topology(self):
        sec_dp = {}
        sec_dp['dp_id'] = self.sec_dpid
        sec_dp['interfaces'] = self._make_sec_interfaces()
        return sec_dp

    def _has_sec_switch(self):
        return self.sec_dpid and self.sec_port

    def _make_base_network_topology(self):
        assert self.pri, 'pri dataplane not configured'
        dps = {}
        dps['pri'] = self._make_pri_topology()
        if self._has_sec_switch():
            dps['sec'] = self._make_sec_topology()
        topology = {}
        topology['dps'] = dps
        topology['vlans'] = self._make_vlan_description(10)
        topology['include'] = self._make_acl_include()
        return topology

    def _make_vlan_description(self, vlan_id):
        return {
            vlan_id: {
                'unicast_flood': False
            }
        }

    def get_network_topology(self):
        """Return the current faucet network topology"""
        return copy.deepcopy(self.topology)

    def _generate_acls(self):
        self._generate_main_acls()
        self._generate_port_acls()

    def _get_gw_ports(self, port_set):
        base_port = Gateway.SET_SPACING * port_set
        end_port = base_port + Gateway.NUM_SET_PORTS
        return list(range(base_port, end_port))

    def _get_bcast_ports(self, port_set):
        return [1, self._SWITCH_LOCAL_PORT] + self._get_gw_ports(port_set)

    def _generate_switch_local_acls(self, portset_acls, local_acl):
        all_ports = []
        if self.ext_ofip:
            for port_set in range(1, self.sec_port):
                self._add_acl_rule(portset_acls[port_set], ports=[self._SWITCH_LOCAL_PORT],
                                   ipv4_dst=self.ext_ofip, dl_type=self.IPV4_DL_TYPE)
                all_ports += self._get_gw_ports(port_set)

        self._add_acl_rule(local_acl, ports=all_ports)

    def _generate_port_target_acls(self, portset_acls):
        port_set_mirrors = {}
        for target in self._port_targets.values():
            port_no = target['port']
            port_set = target['port_set']
            target_mac = target['mac']
            mirror_port = self.mirror_port(port_no)
            port_set_mirrors.setdefault(port_set, []).append((target_mac, mirror_port))
            self._add_acl_rule(portset_acls[port_set], dl_dst=target_mac,
                               ports=[mirror_port], allow=1)
            LOGGER.debug("mirror %s to %s for %s set %s",
                         target_mac, mirror_port, port_no, port_set)
        return port_set_mirrors

    def _generate_mirror_acls(self, port_set_mirrors, incoming_acl, portset_acls):
        for port_set in port_set_mirrors:
            mirror_tuples = port_set_mirrors[port_set]
            mirror_ports = [tuple[1] for tuple in mirror_tuples]
            vlan = self._port_set_vlan(port_set)
            LOGGER.debug("mirroring vlan %s to %s", vlan, mirror_ports)
            for src_mac, src_mirror in mirror_tuples:
                self._add_acl_rule(incoming_acl, dl_src=src_mac, dl_dst=self.BROADCAST_MAC,
                                   vlan_vid=self._NO_VLAN, ports=copy.copy(mirror_ports))
                for dst_mac, dst_mirror in mirror_tuples:
                    if dst_mac != src_mac:
                        self._add_acl_rule(incoming_acl, dl_src=src_mac, dl_dst=dst_mac,
                                           vlan_vid=self._NO_VLAN, ports=[src_mirror, dst_mirror])
                self._add_acl_rule(incoming_acl, dl_src=src_mac,
                                   vlan_vid=self._NO_VLAN, ports=[src_mirror])

            bcast_mirror_ports = mirror_ports + [self._SWITCH_LOCAL_PORT]
            self._add_acl_rule(portset_acls[port_set], dl_dst=self.BROADCAST_MAC,
                               ports=bcast_mirror_ports, allow=1)

    def _generate_main_acls(self):
        incoming_acl = []
        portset_acls = {}
        secondary_acl = []
        local_acl = []
        acls = {}

        for port_set in range(1, self.sec_port):
            portset_acls[port_set] = []

        self._generate_switch_local_acls(portset_acls, local_acl)

        port_set_mirrors = self._generate_port_target_acls(portset_acls)

        self._generate_mirror_acls(port_set_mirrors, incoming_acl, portset_acls)

        self._add_acl_rule(incoming_acl, allow=1)
        acls[self.INCOMING_ACL_FORMAT % self.pri_name] = incoming_acl

        self._add_acl_rule(secondary_acl, allow=1)
        acls[self.INCOMING_ACL_FORMAT % self.sec_name] = secondary_acl

        for port_set in range(1, self.sec_port):
            self._add_acl_rule(portset_acls[port_set], allow=1)
            acls[self.PORTSET_ACL_FORMAT % (self.pri_name, port_set)] = portset_acls[port_set]

        acls[self.LOCAL_ACL_FORMAT % (self.pri_name)] = local_acl

        pri_acls = {}
        pri_acls["acls"] = acls
        self._write_main_acls(pri_acls)

    def _write_main_acls(self, pri_acls):
        filename = self.INST_FILE_PREFIX + self.DP_ACL_FILE_FORMAT
        LOGGER.debug('Writing updated pri acls to %s', filename)
        self._write_acl_file(filename, pri_acls)

    def _write_acl_file(self, filename, pri_acls):
        directory = os.path.dirname(filename)
        os.makedirs(directory, exist_ok=True)
        with open(filename, "w") as output_stream:
            yaml.safe_dump(pri_acls, stream=output_stream)

    def _maybe_apply(self, target, keyword, origin, source=None):
        source_keyword = source if source else keyword
        if source_keyword in origin:
            assert not keyword in target, 'duplicate acl rule keyword %s' % keyword
            target[keyword] = origin[source_keyword]

    def _make_acl_rule(self, **kwargs):
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
        self._maybe_apply(subrule, 'dl_type', kwargs)
        self._maybe_apply(subrule, 'dl_src', kwargs)
        self._maybe_apply(subrule, 'dl_dst', kwargs)
        self._maybe_apply(subrule, 'vlan_vid', in_vlan)
        self._maybe_apply(subrule, 'vlan_vid', kwargs)
        self._maybe_apply(subrule, 'ipv4_dst', kwargs)

        rule = {}
        rule['rule'] = subrule

        return rule

    def _add_acl_rule(self, acl, **kwargs):
        acl.append(self._make_acl_rule(**kwargs))

    def _prepend_acl_rule(self, acl, **kwargs):
        acl.insert(0, self._make_acl_rule(**kwargs))

    def _generate_port_acls(self):
        for port in range(1, self.sec_port):
            self._generate_port_acl(port)

    def _generate_port_acl(self, port):
        target_mac = None
        rules = []

        if self._device_specs and port in self._port_targets:
            target = self._port_targets[port]
            target_mac = target['mac']
            self._add_acl_port_rules(rules, target_mac, port)

        LOGGER.debug('match port %s to mac %s', port, target_mac)

        filename = self.INST_FILE_PREFIX + self.PORT_ACL_FILE_FORMAT % (self.sec_name, port)
        if target_mac:
            assert self._append_acl_template(rules, 'baseline'), 'Missing ACL template baseline'
            self._append_device_default_allow(rules, target_mac)
            self._write_port_acl(port, rules, filename)
        else:
            self._write_port_acl(port, self._make_default_acl_rules(), filename)

        return target_mac

    def _write_port_acl(self, port, rules, filename):
        LOGGER.info("Writing port acl file %s", filename)
        acl_name = self.PORT_ACL_NAME_FORMAT % (self.sec_name, port)
        acls = {}
        acls[acl_name] = rules
        port_acl = {}
        port_acl['acls'] = acls
        directory = os.path.dirname(filename)
        os.makedirs(directory, exist_ok=True)
        with open(filename, "w") as output_stream:
            yaml.safe_dump(port_acl, stream=output_stream)

    def _get_device_type(self, target_mac):
        device_macs = self._device_specs['macAddrs']
        if target_mac not in device_macs:
            LOGGER.info("No device spec found for %s", target_mac)
            return 'default'
        device_info = device_macs[target_mac]
        return device_info['type'] if 'type' in device_info else 'default'

    def _add_acl_port_rules(self, rules, target_mac, port):
        device_type = self._get_device_type(target_mac)
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

    def device_group_size(self, group_name):
        """Return the size of the device group"""
        if not self._device_specs:
            return 1
        mac_map = self._device_specs['macAddrs']
        count = 0
        for target_mac in mac_map:
            if mac_map[target_mac].get('group') == group_name:
                count += 1
        return count if count else 1

    def _make_default_allow_rule(self):
        actions = {'allow': 1}
        subrule = {'actions': actions}
        return {'rule': subrule}

    def _append_augmented_rule(self, rules, acl, targets=None):
        if targets is None:
            rules.append(self._augment_sec_port_acl(acl, None, None))
            return

        dl_dst = self.BROADCAST_MAC
        ports = [target['port'] for target in targets]
        rules.append(self._augment_sec_port_acl(acl, ports, dl_dst))

        for target in targets:
            rules.append(self._augment_sec_port_acl(acl, [target['port']], target['mac']))

    def _augment_sec_port_acl(self, acls, ports, dl_dst):
        acls = copy.deepcopy(acls)
        actions = acls['rule']['actions']
        assert not 'output' in actions, 'output actions explicitly defined'
        if actions['allow']:
            out_ports = (ports + [self.sec_port]) if ports else [self.sec_port]
            actions['output'] = {'ports': out_ports}
            if dl_dst:
                acls['rule']['dl_dst'] = dl_dst
            udp_src = acls['rule'].get('udp_src')
            is_dhcp = int(udp_src) == 68 if udp_src else False
            if ports is not None and not is_dhcp:
                del actions['allow']
        return acls

    def _append_device_default_allow(self, rules, target_mac):
        device_spec = self._device_specs['macAddrs'].get(target_mac)
        if device_spec and 'default_allow' in device_spec:
            allow_action = 1 if device_spec['default_allow'] else 0
            actions = {'allow': allow_action}
            subrule = {'actions': actions}
            subrule['description'] = "device_spec default_allow"
            acl = {'rule': subrule}
            self._append_augmented_rule(rules, acl)

    def _get_acl_template(self, device_type):
        filename = self.TEMPLATE_FILE_FORMAT % device_type
        if not self._device_specs:
            return None
        return self._load_file(filename)

    def _append_acl_template(self, rules, device_type, target_mac=None):
        template_acl = self._get_acl_template(device_type)
        if not template_acl:
            return False
        template_key = self.FROM_ACL_KEY_FORMAT % device_type
        for acl in template_acl['acls'][template_key]:
            new_rule = acl['rule']
            self._resolve_template_field(new_rule, 'dl_src', target_mac=target_mac)
            target = self._resolve_template_field(new_rule, 'nw_dst')
            targets = self._resolve_targets(target, target_mac, new_rule)
            self._append_augmented_rule(rules, acl, targets)
        return True

    def _resolve_targets(self, target, src_mac, src_rule):
        if not target or not target.startswith(self.CTL_PREFIX):
            return None
        controller = target[len(self.CTL_PREFIX):]
        bridge = self._device_specs['macAddrs'][src_mac]
        if 'controllers' not in bridge:
            return None
        if controller not in bridge['controllers']:
            return None
        middle = bridge['controllers'][controller]['controlees']
        if controller not in middle:
            return None
        target_macs = middle[controller]['mac_addrs']
        target_ports = []
        for target_mac in target_macs:
            if self._allow_target_mac(target_mac, src_rule, controller):
                LOGGER.debug('allow_target %s', target_mac)
                for port_target in self._port_targets.values():
                    if port_target['mac'] == target_mac:
                        LOGGER.debug('allow_target %s on %s', target_mac, port_target['port'])
                        target_ports.append(port_target)
        return target_ports

    def _allow_target_mac(self, target_mac, src_rule, controller):
        device_type = self._get_device_type(target_mac)
        template_acl = self._get_acl_template(device_type)
        if not template_acl:
            return False
        device_macs = self._device_specs['macAddrs']
        if target_mac not in device_macs:
            return False
        device_info = device_macs[target_mac]
        device_type = device_info['type'] if 'type' in device_info else 'default'
        template_key = self.TO_ACL_KEY_FORMAT % device_type
        for acl in template_acl['acls'][template_key]:
            target_rule = acl['rule']
            if self._rule_match(src_rule, target_rule, controller):
                return True
        return False

    def _rule_match(self, src_rule, dst_rule, controller):
        LOGGER.debug('Checking rule match for controller %s', controller)
        dst_ctl = self.CTL_PREFIX + controller
        if dst_rule.get('nw_src') != dst_ctl:
            return False
        match = self._conditional_match(src_rule, dst_rule, 'udp_src')
        match = match and self._conditional_match(src_rule, dst_rule, 'udp_dst')
        match = match and self._conditional_match(src_rule, dst_rule, 'tcp_src')
        match = match and self._conditional_match(src_rule, dst_rule, 'tcp_dst')
        return match

    def _conditional_match(self, src_rule, dst_rule, field):
        src = src_rule.get(field)
        dst = dst_rule.get(field)
        if src and dst:
            return src == dst
        return True

    def _resolve_template_field(self, rule, field, target_mac=None):
        if field not in rule:
            return None
        placeholder = rule[field]
        if placeholder.startswith(self.MAC_PREFIX):
            rule[field] = target_mac
        elif placeholder.startswith(self.DNS_PREFIX):
            del rule[field]
        elif placeholder.startswith(self.CTL_PREFIX):
            del rule[field]
        return placeholder
