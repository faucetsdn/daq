"""Faucet-specific topology module"""

import copy
import os
import yaml

import logger
from env import DAQ_RUN_DIR, DAQ_LIB_DIR

LOGGER = logger.get_logger('topology')


class FaucetTopology:
    """Topology manager specific to FAUCET configs"""

    MAC_PREFIX = "@mac:"
    DNS_PREFIX = "@dns:"
    CTL_PREFIX = "@ctrl:"
    INST_FILE_PREFIX = DAQ_RUN_DIR
    BROADCAST_MAC = "ff:ff:ff:ff:ff:ff"
    IPV4_DL_TYPE = "0x0800"
    ARP_DL_TYPE = "0x0806"
    LLDP_DL_TYPE = "0x88cc"
    PORT_ACL_NAME_FORMAT = "dp_%s_port_%d_acl"
    DP_ACL_FILE_FORMAT = "dp_port_acls.yaml"
    PORT_ACL_FILE_FORMAT = os.path.join("port_acls", "dp_%s_port_%d_acl.yaml")
    TEMPLATE_FILE_FORMAT = os.path.join(INST_FILE_PREFIX, "acl_templates", "template_%s_acl.yaml")
    FROM_ACL_KEY_FORMAT = "@from:template_%s_acl"
    TO_ACL_KEY_FORMAT = "@to:template_%s_acl"
    INCOMING_ACL_FORMAT = "dp_%s_incoming_acl"
    PORTSET_ACL_FORMAT = "dp_%s_portset_%d_acl"
    LOCAL_ACL_FORMAT = "dp_%s_local_acl"
    _DEFAULT_SEC_TRUNK_NAME = "trunk_sec"
    _MIRROR_IFACE_FORMAT = "mirror-%d"
    _MIRROR_PORT_BASE = 1000
    _SWITCH_LOCAL_PORT = _MIRROR_PORT_BASE
    _LOCAL_VLAN = 1000
    _DUMP_VLAN = 999
    PRI_DPID = 1
    PRI_TRUNK_PORT = 1
    VXLAN_SEC_DPID = 2
    VXLAN_SEC_TRUNK_PORT = 1
    PRI_TRUNK_NAME = 'trunk_pri'
    _NO_VLAN = "0x0000/0x1000"
    _EXT_STACK = 'EXT_STACK'
    _OFPP_IN_PORT = 0xfffffff8
    _DOT1X_ETH_TYPE = 0x888e
    _DEFAULT_GAUGE_VARZ_PORT = 9303
    _VXLAN_ACL = 'vxlan'
    _COUPLER_ACL = 'vxlan_coupler'

    def __init__(self, config):
        self.config = config
        self.pri = None
        self.pri_name = None
        self.sec_name = 'sec'
        switch_setup = self.config.get('switch_setup', {})
        self.sec_port = int(switch_setup['uplink_port'])
        self.sec_dpid = int(switch_setup.get('of_dpid', 0))
        self.ext_ofip = switch_setup.get('lo_addr')
        self.ext_intf = switch_setup.get('data_intf') if switch_setup.get('ctrl_intf') else None
        self._native_faucet = switch_setup.get('native')
        self._ext_faucet = switch_setup.get('model') == self._EXT_STACK
        self._gauge_varz_port = int(switch_setup.get('varz_port_2', self._DEFAULT_GAUGE_VARZ_PORT))
        self._device_specs = self._load_device_specs()
        self._port_targets = {}
        self._set_devices = {}
        self._egress_vlan = self.config.setdefault('run_trigger', {}).get('egress_vlan')
        self._native_vlan = self.config.setdefault('run_trigger', {}).get('native_vlan')
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
        self._run_faucet()
        self._run_faucet(as_gauge=True)

    def stop(self):
        """Stop this instance"""
        if self._ext_faucet and not self._native_faucet:
            return
        self._run_faucet(kill=True)
        self._run_faucet(kill=True, as_gauge=True)

    def _run_faucet(self, kill=False, as_gauge=False):
        process_name = 'gauge' if as_gauge else 'faucet'
        native_arg = ' native' if self._native_faucet else ''
        gauge_arg = ' gauge' if as_gauge else ''
        kill_arg = ' kill' if kill else ''

        LOGGER.info('Starting%s%s %s...', native_arg, kill_arg, process_name)
        cmd = '%s/cmd/faucet%s%s%s && echo FAUCET_EVENT_SOCK=$FAUCET_EVENT_SOCK && echo SUCCESS' % (
            DAQ_LIB_DIR, native_arg, kill_arg, gauge_arg)

        output = self.pri.cmd(cmd)
        if not output.strip().endswith('SUCCESS'):
            LOGGER.error('%s output:\n%s', process_name, output)
            assert False, '%s failed' % process_name
        if as_gauge:
            return
        sock = list(filter(lambda line: line.startswith('FAUCET_EVENT_SOCK='), output.split('\n')))
        if not sock:
            assert False, 'FAUCET_EVENT_SOCK not found after exposing faucet'
        os.environ['FAUCET_EVENT_SOCK'] = sock[0].split('=')[1].strip()

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

    def _populate_set_devices(self, device, port_set):
        device_set = device.gateway.port_set if device.gateway else port_set
        assert port_set == device_set or not port_set
        if port_set:
            self._set_devices.setdefault(device_set, set()).add(device)
        elif device_set in self._set_devices:
            self._set_devices[device_set].discard(device)
        set_active = bool(self._set_devices.get(device_set))
        vlan = device.vlan if set_active else self._DUMP_VLAN
        LOGGER.info('Setting port set %s to vlan %s', device_set, vlan)
        return device_set, vlan

    def direct_device_traffic(self, device):
        """Modify gateway set's vlan to match triggering vlan"""
        port_set = device.gateway.port_set if device.gateway else None
        device_set, vlan = self._populate_set_devices(device, port_set)
        LOGGER.info('Directing %s/%s to %s (%s)', port_set, device_set, vlan, device.port.vxlan)
        self._ensure_gateway_interfaces(device_set)
        interfaces = self.topology['dps'][self.pri_name]['interfaces']
        if vlan:
            LOGGER.info('Directing device %s port_set %s to vlan %s', device, port_set, vlan)
            for port in self._get_gw_ports(device_set):
                interfaces[port]['native_vlan'] = vlan

        sec_topology = self.topology['dps'].setdefault(self.sec_name, {
            'dp_id': self.VXLAN_SEC_DPID,
            'interfaces': {
                self.VXLAN_SEC_TRUNK_PORT: self._make_sec_trunk_interface()
            }
        })
        sec_interfaces = sec_topology['interfaces']

        LOGGER.info('Direct device %s traffic to %s %s', device.mac, device.port.vxlan, port_set)
        if device.port.vxlan:
            egress_vlan = device.assigned if device.assigned else self._egress_vlan
            if egress_vlan:
                sec_topology['interfaces'][self.VXLAN_SEC_TRUNK_PORT] = (
                    self._make_sec_trunk_interface(addition=(egress_vlan,)))

            if port_set:
                interface = sec_interfaces.setdefault(device.port.vxlan, {})
                if egress_vlan:
                    interface['tagged_vlans'] = [vlan, egress_vlan]
                    incoming_acls = [self._VXLAN_ACL]
                else:
                    interface['native_vlan'] = vlan
                    incoming_acls = ['%s_%s' % (self._COUPLER_ACL, vlan), self._COUPLER_ACL]
                interface['name'] = str(device)
                interface['acls_in'] = list(
                    map(lambda acl: self.INCOMING_ACL_FORMAT % acl, incoming_acls))
            else:
                sec_interfaces.pop(device.port.vxlan, None)

        # This logging statement is used for integration testing.
        LOGGER.info('Configured topology with %d interfaces: %s',
                    len(sec_interfaces), list(sec_interfaces.keys()))

        self._generate_acls()

    def direct_port_traffic(self, device, port_no, target):
        """Direct traffic from a port to specified port set"""
        self._populate_set_devices(device, device.gateway.port_set)
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
        interface = self.topology['dps'][self.sec_name]['interfaces'][port_no]
        interface['native_vlan'] = self._port_set_vlan(port_set)

    def _get_port_vlan(self, port_no):
        port_set = self._port_targets.get(port_no, {}).get('port_set')
        return self._port_set_vlan(port_set)

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

    def _make_local_interface(self):
        interface = {}
        interface['name'] = 'local_switch'
        interface['native_vlan'] = self._LOCAL_VLAN
        interface['acl_in'] = self.LOCAL_ACL_FORMAT % (self.pri_name)
        return interface

    def _make_gw_interface(self, port_set):
        interface = {}
        interface['acl_in'] = self.PORTSET_ACL_FORMAT % (self.pri_name, port_set)
        vlan_id = self._DUMP_VLAN if self._use_vlan_triggers() else self._port_set_vlan(port_set)
        interface['native_vlan'] = vlan_id
        return interface

    def _port_set_vlan(self, port_set):
        return self._LOCAL_VLAN + port_set if port_set else self._DUMP_VLAN

    def _make_in_port_interface(self):
        interface = {}
        interface['description'] = 'OFPP_IN_PORT'
        interface['output_only'] = True
        return interface

    def _make_pri_trunk_interface(self):
        interface = {}
        interface['acl_in'] = self.INCOMING_ACL_FORMAT % self.pri_name
        if self._native_vlan:
            interface['native_vlan'] = self._native_vlan
        else:
            interface['tagged_vlans'] = self._vlan_tags()
        interface['name'] = self.PRI_TRUNK_NAME
        return interface

    def _make_sec_trunk_interface(self, addition=()):
        interface = {}
        interface['acl_in'] = self.INCOMING_ACL_FORMAT % self.sec_name
        interface['tagged_vlans'] = list(set(self._vlan_tags() + list(addition)))
        interface['name'] = self.get_ext_intf() or self._DEFAULT_SEC_TRUNK_NAME
        return interface

    def _use_vlan_triggers(self):
        vlan_range_config = self.config.get("run_trigger", {})
        return bool(vlan_range_config.get("vlan_start"))

    def _vlan_tags(self):
        vlan_range_config = self.config.get("run_trigger", {})
        vlan_start = vlan_range_config.get("vlan_start")
        vlan_end = vlan_range_config.get("vlan_end")
        if self._use_vlan_triggers():
            return [*range(vlan_start, vlan_end + 1)] + [self._LOCAL_VLAN]
        return list(range(self._LOCAL_VLAN, self._LOCAL_VLAN + self.sec_port))

    def _make_default_acl_rules(self):
        rules = []
        if not self._append_acl_template(rules, 'raw'):
            self._append_augmented_rule(rules, self._make_default_allow_rule())
        return rules

    def _make_sec_port_interface(self, port_no):
        interface = {}
        interface['acl_in'] = self.PORT_ACL_NAME_FORMAT % (self.sec_name, port_no)
        vlan_id = self._port_set_vlan(port_no) if self._use_vlan_triggers() else self._DUMP_VLAN
        interface['native_vlan'] = vlan_id
        return interface

    def _make_pri_interfaces(self):
        interfaces = {}
        interfaces[self.PRI_TRUNK_PORT] = self._make_pri_trunk_interface()
        interfaces[self._OFPP_IN_PORT] = self._make_in_port_interface()
        for port_set in range(1, self.sec_port):
            mirror_port = self.mirror_port(port_set)
            interfaces[mirror_port] = self._make_mirror_interface(port_set)
        interfaces[self._SWITCH_LOCAL_PORT] = self._make_local_interface()
        return interfaces

    def _ensure_gateway_interfaces(self, port_set):
        interfaces = self.topology['dps'][self.pri_name]['interfaces']
        LOGGER.debug('Ensuring gateway interfaces for port_set %s', port_set)
        for port in self._get_gw_ports(port_set):
            assert port < self._MIRROR_PORT_BASE, (
                'Port %d conflicts with mirror port %s' % (port, self._MIRROR_PORT_BASE))
            interfaces.setdefault(port, self._make_gw_interface(port_set))

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

    def get_gauge_config(self):
        """Return Gauge config"""
        config = {
            'dbs': {
                'prometheus': {'prometheus_port': self._gauge_varz_port, 'type': 'prometheus'}
            },
            'faucet_configs': ['/etc/faucet/faucet.yaml'],
            'watchers': {
                'flow_table_poller': {'all_dps': True, 'db': 'prometheus', 'type': 'flow_table'},
                'port_stats_poller': {'all_dps': True, 'db': 'prometheus', 'type': 'port_stats'},
                'port_status_poller': {'all_dps': True, 'db': 'prometheus', 'type': 'port_state'}
            }
        }
        return config

    def _generate_acls(self):
        self._generate_main_acls()
        self._generate_port_acls()

    def register_device(self, device):
        """Register a device with the network topology"""

    def _get_gw_ports(self, port_set):
        for device_set in self._set_devices:
            if device_set == port_set:
                LOGGER.debug('Matching devices for port_set %s found', port_set)
                device = next(iter(self._set_devices[device_set]))
                return device.gateway.get_all_gw_ports() if device.gateway else range(0, 0)
        LOGGER.warning('Matching devices for port_set %s not found', port_set)
        return range(0, 0)

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
        targets = list(self._port_targets.values())
        for devices in self._set_devices.values():
            for device in devices:
                if device and device.gateway:
                    target = {'port': None, 'port_set': device.gateway.port_set, 'mac': device.mac}
                    targets.append(target)
        for target in targets:
            port_no = target['port']
            port_set = target['port_set']
            target_mac = target['mac']
            # In host.py, mirror port on which tcpdump is run is set to network.tap_intf, which
            # is the pri trunk port if no target ports are specified.
            mirror_port = self.mirror_port(port_no) if port_no else self.PRI_TRUNK_PORT
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

    def _add_dhcp_reflectors(self, acl_list):
        if not self._ext_faucet:
            return
        for devices in self._set_devices.values():
            for device in devices:
                # Rule for DHCP request to server. Convert device vlan to egress vlan.
                egress_vlan = device.assigned if device.assigned else self._egress_vlan
                LOGGER.debug('Reflecting %s dhcp with %s/%s', device.mac, device.vlan, egress_vlan)
                self._add_acl_rule(acl_list, dl_type='0x800', nw_proto=17, udp_src=68, udp_dst=67,
                                   vlan_vid=device.vlan, swap_vid=egress_vlan,
                                   port=self._OFPP_IN_PORT)
                self._add_acl_rule(acl_list, dl_type='0x800', dl_dst=device.mac, nw_proto=17,
                                   udp_src=67, udp_dst=68, vlan_vid=egress_vlan,
                                   swap_vid=device.vlan, port=self._OFPP_IN_PORT, allow=True)

        # Allow any unrecognized DHCP requests for learning, but don't reflect.
        self._add_acl_rule(acl_list, dl_type='0x800', allow=True,
                           nw_proto=17, udp_src=68, udp_dst=67)

        # Deny any unrecognized replies.
        self._add_acl_rule(acl_list, dl_type='0x800', allow=False,
                           nw_proto=17, udp_src=67, udp_dst=68)

    def _add_dot1x_incoming_rule(self, incoming_acl, secondary_acl):
        for devices in self._set_devices.values():
            for device in devices:
                if device and device.gateway:
                    vlan = device.vlan if device.vlan else self._get_port_vlan(device.port.port_no)
                    test_ports = device.gateway.get_possible_test_ports()
                    if test_ports:
                        self._add_dot1x_allow_rule(incoming_acl, test_ports, vlan_vid=vlan)
                    device_port = device.port.port_no
                    if device_port:
                        self._add_dot1x_allow_rule(secondary_acl, [device_port], in_vlan=vlan)

    def _add_dot1x_vxlan_acl(self, acls):
        for devices in self._set_devices.values():
            for device in devices:
                if device and device.vlan:
                    acl_name = 'vxlan_coupler_%s' % device.vlan
                    dot1x_rule = []
                    self._add_dot1x_allow_rule(dot1x_rule, [1], out_vid=device.vlan)
                    acls[self.INCOMING_ACL_FORMAT % acl_name] = dot1x_rule

    # pylint: disable=too-many-arguments
    def _add_dot1x_allow_rule(self, acl, ports, vlan_vid=None, out_vid=None, in_vlan=None):
        """Add dot1x reflection rule to acl"""
        if vlan_vid:
            self._add_acl_rule(acl, eth_type=self._DOT1X_ETH_TYPE, ports=ports, vlan_vid=vlan_vid)
        elif out_vid:
            self._add_acl_rule(acl, eth_type=self._DOT1X_ETH_TYPE, ports=ports, out_vid=out_vid)
        elif in_vlan:
            self._add_acl_rule(acl, eth_type=self._DOT1X_ETH_TYPE, ports=ports, in_vlan=in_vlan)

    def _generate_main_acls(self):
        incoming_acl = []
        portset_acls = {}
        secondary_acl = []
        local_acl = []
        acls = {}

        self._add_dot1x_incoming_rule(incoming_acl, secondary_acl)

        for port_set in range(1, self.sec_port):
            portset_acls[port_set] = []

        self._generate_switch_local_acls(portset_acls, local_acl)

        port_set_mirrors = self._generate_port_target_acls(portset_acls)

        self._generate_mirror_acls(port_set_mirrors, incoming_acl, portset_acls)

        self._add_dhcp_reflectors(incoming_acl)
        self._add_acl_rule(incoming_acl, allow=1)
        acls[self.INCOMING_ACL_FORMAT % self.pri_name] = incoming_acl

        self._add_acl_rule(secondary_acl, allow=1)
        acls[self.INCOMING_ACL_FORMAT % self.sec_name] = secondary_acl

        acls[self.INCOMING_ACL_FORMAT % self._VXLAN_ACL] = [
            self._make_acl_rule(ports=[self.VXLAN_SEC_TRUNK_PORT])]
        acls[self.INCOMING_ACL_FORMAT % self._COUPLER_ACL] = [
            self._make_acl_rule(ports=[self.VXLAN_SEC_TRUNK_PORT], allow=True)]
        self._add_dot1x_vxlan_acl(acls)

        for port_set in range(1, self.sec_port):
            vlan = self._port_set_vlan(port_set)
            if port_set in self._set_devices:
                portset_device = next(iter(self._set_devices[port_set]))
                if portset_device.vlan:
                    vlan = portset_device.vlan
            self._add_dot1x_allow_rule(portset_acls[port_set], [self.PRI_TRUNK_PORT], out_vid=vlan)
            self._add_acl_rule(portset_acls[port_set], allow=1)
            acls[self.PORTSET_ACL_FORMAT % (self.pri_name, port_set)] = portset_acls[port_set]

        acls[self.LOCAL_ACL_FORMAT % (self.pri_name)] = local_acl

        pri_acls = {}
        pri_acls["acls"] = acls
        self._write_main_acls(pri_acls)

    def _write_main_acls(self, pri_acls):
        filename = os.path.join(self.INST_FILE_PREFIX, self.DP_ACL_FILE_FORMAT)
        LOGGER.debug('Writing updated pri acls to %s', filename)
        self._write_acl_file(filename, pri_acls)

    def _write_acl_file(self, filename, pri_acls):
        directory = os.path.dirname(filename)
        os.makedirs(directory, exist_ok=True)
        LOGGER.debug('Writing acl file to %s', filename)
        with open(filename, "w") as output_stream:
            yaml.safe_dump(pri_acls, stream=output_stream)

    def _maybe_apply(self, target, keyword, origin, source=None):
        source_keyword = source if source else keyword
        if source_keyword in origin and origin[source_keyword] is not None:
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
        self._maybe_apply(output, 'vlan_vid', kwargs, 'out_vid')
        self._maybe_apply(output, 'swap_vid', kwargs)
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
        self._maybe_apply(subrule, 'nw_proto', kwargs)
        self._maybe_apply(subrule, 'udp_src', kwargs)
        self._maybe_apply(subrule, 'udp_dst', kwargs)
        self._maybe_apply(subrule, 'vlan_vid', in_vlan)
        self._maybe_apply(subrule, 'vlan_vid', kwargs)
        self._maybe_apply(subrule, 'ipv4_dst', kwargs)
        self._maybe_apply(subrule, 'eth_type', kwargs)

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

        vlan = self._get_port_vlan(port)
        self._add_dot1x_allow_rule(rules, [self.sec_port], out_vid=vlan)

        if self._device_specs and port in self._port_targets:
            target = self._port_targets[port]
            target_mac = target['mac']
            self._add_acl_port_rules(rules, target_mac, port)

        LOGGER.debug('match port %s to mac %s', port, target_mac)

        file_name = self.PORT_ACL_FILE_FORMAT % (self.sec_name, port)
        file_path = os.path.join(self.INST_FILE_PREFIX, file_name)
        if target_mac:
            assert self._append_acl_template(rules, 'baseline'), 'Missing ACL template baseline'
            self._append_device_default_allow(rules, target_mac)
        else:
            rules.extend(self._make_default_acl_rules())

        self._write_port_acl(port, rules, file_path)

        return target_mac

    def _write_port_acl(self, port, rules, filename):
        LOGGER.debug("Writing port acl file %s", filename)
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

    def device_group_for(self, device):
        """Return the target device group for the given device"""
        if self._ext_faucet:
            return 'vlan-%s' % device.vlan
        target_mac = device.mac
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
