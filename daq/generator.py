"""Faucet network topology generator"""

import copy
import os
import sys
import yaml

from daq import DAQ
import logger

LOGGER = logger.get_logger('generator')

class TopologyGenerator():
    """Topology generator for Faucet top-level configs"""

    _YAML_POSTFIX = '.yaml'
    _UNIFORM_ACL_NAME = 'uniform_acl'
    _UNIFORM_FILE_NAME = 'uniform.yaml'
    _INCLUDE_SET = [_UNIFORM_FILE_NAME]

    def __init__(self, daq_config):
        self.config = daq_config.config
        daq_config.configure_logging()
        self._setup = None
        self._site = None

    def process(self):
        """Process a configured generator"""
        if 'raw_topo' in self.config:
            self._normalize_raw_topo()
        elif 'site_config' in self.config:
            self._generate_topology()
        else:
            LOGGER.error('No valid generator options found')
            return -1
        return 0

    def _normalize_raw_topo(self):
        source_dir = self.config.get('raw_topo')
        assert source_dir, 'raw_topo not defined'
        topo_dir = self.config.get('topo_dir', 'inst')
        if not os.path.exists(topo_dir):
            os.makedirs(topo_dir)
        configs = {}
        for filename in os.listdir(source_dir):
            if not filename.endswith(self._YAML_POSTFIX):
                LOGGER.info('Skipping non-yaml file %s', filename)
                continue
            in_path = os.path.join(source_dir, filename)
            configs[filename] = self._load_config(in_path)
        self._flatten_configs(configs)
        for config in configs:
            self._write_yaml(topo_dir, config, configs[config])

    def _flatten_configs(self, configs):
        faucet_conf = configs['faucet.yaml']
        assert 'include-optional' not in faucet_conf, 'can not normalize include-optional'
        if 'include' not in faucet_conf:
            LOGGER.info('No includes found.')
            return
        include_set = set(faucet_conf['include'])
        for target in faucet_conf['include']:
            assert target in configs, 'config target %s not found' % target
            if target in self._INCLUDE_SET:
                LOGGER.info('Preserving include entry %s', target)
            else:
                LOGGER.info('Flattening include entry %s', target)
                self._flatten_include(faucet_conf, configs[target])
                self._delete_config_file(target)
                include_set.remove(target)
                del configs[target]
        for exclude in self._INCLUDE_SET:
            assert exclude not in faucet_conf, 'file %s should not be included' % exclude
        if include_set:
            faucet_conf['include'] = list(include_set)
        else:
            del faucet_conf['include']

    def _flatten_include(self, faucet_conf, target_conf):
        keys = set(target_conf.keys())
        keys.discard('version')
        for part in keys:
            assert part not in faucet_conf, 'faucet config already contains %s' % faucet_conf
            faucet_conf[part] = target_conf[part]

    def _delete_config_file(self, target):
        topo_dir = self.config.get('topo_dir', 'inst')
        target_path = os.path.join(topo_dir, target)
        if os.path.exists(target_path):
            LOGGER.info('Removing %s', target_path)
            os.remove(target_path)

    def _generate_topology(self):
        setup_config = self.config.get('topo_setup')
        self._setup = self._load_config(setup_config)
        site_config = self.config.get('site_config')
        assert site_config, 'site_config not defined'
        self._site = self._load_config(site_config)
        for domain in self._get_all_domains():
            target = self._make_target(domain)
            self._write_config(target, 'faucet.yaml', self._make_faucet(domain))
            self._write_config(target, 'gauge.yaml', self._make_gauge(domain))
            self._write_config(target, self._UNIFORM_FILE_NAME, self._make_uniform())

    def _load_config(self, path):
        LOGGER.info('Loading %s', path)
        with open(path) as stream:
            return yaml.safe_load(stream)

    def _write_config(self, target, filename, data):
        topo_base = self.config.get('topo_dir')
        topo_dir = os.path.join(topo_base, self._get_ctl_name(target))
        self._write_yaml(topo_dir, filename, data)

    def _write_yaml(self, topo_dir, filename, data):
        if not os.path.exists(topo_dir):
            os.makedirs(topo_dir)
        out_path = os.path.join(topo_dir, filename)
        LOGGER.info('Writing output file %s', out_path)
        with open(out_path, 'w') as stream:
            yaml.safe_dump(data, stream=stream)

    def _get_all_domains(self):
        return self._site['tier1']['domains'].keys()

    def _make_target(self, domain):
        domain_dp = self._site['tier1']['domains'][domain]
        return {
            'location': domain_dp.get('location', ''),
            'domain': domain
        }

    def _make_uniform(self):
        pre_rules = self._make_uniform_rules(self._setup['pre_acls'])
        site_rules = self._make_uniform_rules(self._site.get('uniform_acls'))
        post_rules = self._make_uniform_rules(self._setup['post_acls'])
        return {
            "acls": {
                self._UNIFORM_ACL_NAME: pre_rules + site_rules + post_rules
            }
        }

    def _make_uniform_rules(self, entries):
        if not entries:
            return []
        rules = []
        for entry in entries:
            entry = copy.deepcopy(entry)

            allow = entry.get('allow', True)
            if 'allow' in entry:
                del entry['allow']
            entry['actions'] = {
                'allow': 1 if allow else 0
            }

            if not 'dl_type' in entry:
                entry['dl_type'] = '0x0800'

            if 'tcp_src' in entry or 'tcp_dst' in entry:
                entry['nw_proto'] = 6
            if 'udp_src' in entry or 'udp_dst' in entry:
                entry['nw_proto'] = 17

            rules.append({
                'rule': entry
            })
        return rules

    def _make_faucet(self, domain):
        return {
            'vlans': self._make_vlans(),
            'dps': self._make_dps(domain),
            'include': [self._UNIFORM_FILE_NAME],
            'version': 2
        }

    def _make_gauge(self, domain):
        db_type = self._setup['gauge']['db_type']
        return {
            'dbs': {
                db_type: self._setup['db_types'][db_type]
            },
            'faucet_configs': [self._setup['faucet_yaml']],
            'watchers': {
                'flow_table': self._make_gauge_watcher(domain, 'flow_table'),
                'port_stats': self._make_gauge_watcher(domain, 'port_stats')
            }
        }

    def _make_gauge_watcher(self, domain, watcher_type):
        return {
            'db': self._setup['gauge']['db_type'],
            'interval': self._setup['gauge']['interval'],
            'type': watcher_type,
            'dps': self._get_all_dp_names(domain)
        }

    def _get_all_dp_names(self, domain):
        t1_dp_names = list(self._make_t1_dps(domain).keys())
        t2_dp_names = list(self._make_t2_dps(domain).keys())
        return t1_dp_names + t2_dp_names

    def _maybe_add(self, var, key, value):
        if value is not None:
            var[key] = value

    def _maybe_update(self, var, target):
        if target is not None:
            var.update(target)

    def _make_t1_dps(self, domain):
        t1_conf = self._site['tier1']['domains'][domain]
        dp_name = self._get_t1_dp_name(domain)
        stack = {
            'priority': 1
        }
        self._maybe_add(stack, 'upstream_lacp', self._site['tier1'].get('upstream_lacp'))
        return {
            dp_name: {
                'dp_id': t1_conf['dp_id'],
                'combinatorial_port_flood': self._setup['combinatorial_port_flood'],
                'faucet_dp_mac': self._make_faucet_dp_mac(domain, 1),
                'hardware': self._make_t1_hardware(domain),
                'lacp_timeout': self._setup['lacp_timeout'],
                'lldp_beacon': self._get_switch_lldp_beacon(),
                'interfaces': self._make_t1_dp_interfaces(t1_conf, domain),
                'stack': stack
            }
        }

    def _make_t1_hardware(self, domain):
        t1_conf = self._site['tier1']
        if 'defaults' in t1_conf:
            if 'hardware' in t1_conf['defaults']:
                return t1_conf['defaults']['hardware']
        return self._setup['default_hardware']

    def _make_faucet_dp_mac(self, domain, tier):
        return self._setup['faucet_dp_mac_format'] % (int(domain), tier)

    def _make_t1_dp_interfaces(self, t1_conf, domain):
        interfaces = {}
        for uplink_port in self._site['tier1']['uplink_ports']:
            interfaces.update({uplink_port: self._make_uplink_interface(domain)})
        interfaces.update(self._make_t1_stack_interfaces(domain))
        return interfaces

    def _make_uplink_interface(self, domain):
        upstream_lacp = self._site['tier1'].get('upstream_lacp')
        interface = {
            'description': self._setup['egress_description']
        }
        if self._setup['loop_protect_external']:
            interface['loop_protect_external'] = True
        if self._site['tier1'].get('uplink_native'):
            interface['native_vlan'] = self._site['vlan_id']
        else:
            interface['tagged_vlans'] = [self._site['vlan_id']]
        self._maybe_update(interface, self._setup.get('uplink_iface'))
        self._maybe_add(interface, 'lacp', upstream_lacp)
        self._maybe_add(interface, 'name', self._site['tier1']['domains'][domain].get('name'))
        return interface

    def _make_device_interface(self):
        return {
            'description': self._setup['device_description'],
            'acl_in': self._UNIFORM_ACL_NAME,
            'native_vlan': self._site['vlan_id']
        }

    def _make_t1_stack_interfaces(self, domain):
        interfaces = {}
        tier1_ports = self._site['tier2']['tier1_ports']
        for tier1_port in tier1_ports:
            tier2_spec = tier1_ports[tier1_port]
            if tier2_spec['domain'] == domain:
                interfaces.update({
                    tier1_port: self._make_t1_stack_interface(tier2_spec)
                })
            else:
                interfaces.update({
                    tier1_port: self._make_t2_cross_interface()
                })

        return interfaces

    def _make_t1_stack_interface(self, tier2_spec):
        port = tier2_spec['stack_port']
        dp_name = self._get_t2_dp_name(tier2_spec)
        return {
            'lldp_beacon': self._get_port_lldp_beacon(),
            'receive_lldp': self._setup['receive_lldp'],
            'stack': {
                'dp': dp_name,
                'port': port
            }
        }

    def _make_t2_cross_interface(self):
        return {
            'loop_protect_external': self._setup['loop_protect_external'],
            'tagged_vlans': [self._site['vlan_id']]
        }

    def _make_t2_dps(self, domain):
        dps = {}
        t1_ports = self._site['tier2']['tier1_ports']
        for t1_port in t1_ports:
            t2_conf = t1_ports[t1_port]
            if t2_conf['domain'] == domain:
                dp_name = self._get_t2_dp_name(t2_conf)
                dps.update({dp_name: self._make_t2_dp(t2_conf, t1_port)})
        return dps

    def _make_t2_dp(self, t2_conf, t1_port):
        t2_defaults = self._site['tier2']['defaults']
        return {
            'dp_id': t2_conf['dp_id'],
            'combinatorial_port_flood': self._setup['combinatorial_port_flood'],
            'faucet_dp_mac': self._make_faucet_dp_mac(t2_conf['domain'], 2),
            'hardware': self._make_t2_hardware(t2_defaults, t2_conf),
            'lacp_timeout': self._setup['lacp_timeout'],
            'lldp_beacon': self._get_switch_lldp_beacon(),
            'interface_ranges': self._make_t2_interface_ranges(),
            'interfaces': self._make_t2_interfaces(t2_conf, t1_port)
        }

    def _make_t2_hardware(self, defaults, conf):
        if 'hardware' in conf:
            return conf['hardware']
        if 'hardware' in defaults:
            return defaults['hardware']
        return self._setup['default_hardware']

    def _make_t2_interface_ranges(self):
        interface_ranges = self._site['tier2']['defaults']['device_ports']
        return {interface_ranges: self._make_device_interface()}

    def _make_t2_interfaces(self, t2_conf, t1_port):
        return {
            t2_conf['stack_port']: self._make_t2_stack_interface(t2_conf, t1_port),
            t2_conf['cross_port']: self._make_t2_cross_interface()
        }

    def _make_t2_stack_interface(self, t2_conf, t1_port):
        t1_dp_name = self._get_t1_dp_name(t2_conf['domain'])
        return {
            'lldp_beacon': self._get_port_lldp_beacon(),
            'receive_lldp': self._setup['receive_lldp'],
            'stack': {
                'dp': t1_dp_name,
                'port': t1_port
            }
        }

    def _get_switch_lldp_beacon(self):
        return copy.deepcopy(self._setup['switch_lldp_beacon'])

    def _get_port_lldp_beacon(self):
        return copy.deepcopy(self._setup['port_lldp_beacon'])

    def _get_ctl_name(self, target):
        site_name = self._site['site_name']
        switch_type = self._setup['naming']['control']
        return site_name + switch_type + target.get('location', '') + target['domain']

    def _get_t1_dp_name(self, domain):
        site_name = self._site['site_name']
        switch_type = self._setup['naming']['tier1']
        t1_conf = self._site['tier1']['domains'][domain]
        return site_name + switch_type + t1_conf.get('location', '') + domain

    def _get_t2_dp_name(self, t2_conf):
        site_name = self._site['site_name']
        switch_type = self._setup['naming']['tier2']
        return site_name + switch_type + t2_conf.get('location', '') + t2_conf['domain']

    def _make_vlans(self):
        return {
            self._setup['vlan']['name']: {
                'description': self._setup['vlan']['description'],
                'vid': self._site['vlan_id']
            }
        }

    def _make_dps(self, domain):
        return {**self._make_t1_dps(domain), **self._make_t2_dps(domain)}


if __name__ == '__main__':
    sys.exit(TopologyGenerator(DAQ(sys.argv)).process())
