"""Process ACL states"""

from __future__ import absolute_import

import logger

LOGGER = logger.get_logger('acl')


class AclStateCollector:
    """Processing ACL states for ACL counting"""

    def __init__(self):
        self._switch_configs = {}

    def get_port_acl_count(self, switch, port, port_acl_samples):
        """Return the ACL count for a port"""

        switch_config = self._switch_configs.get(switch)
        if not switch_config:
            LOGGER.warning('Switch not defined in Faucet dps config: %s', switch)
            return {}

        port_config = switch_config.ports.get(port)
        if not port_config:
            LOGGER.warning('Port not defined in Faucet dps config: %s:%s', switch, port)
            return {}

        acls_config = port_config.acls_in
        if not acls_config:
            LOGGER.warning('No ACLs applied to port: %s:%s', switch, port)
            return {}

        return self._get_port_rules_count(switch, port, acls_config[0], port_acl_samples)

    # pylint: disable=protected-access
    def _get_port_rules_count(self, switch, port, acl_config, acl_samples):
        rules_map = {}

        for rule_config in acl_config.rules:
            cookie_num = rule_config.get('cookie')
            if not cookie_num:
                LOGGER.error(
                    'Cookie is not generated for ACL rule: %s, %s',
                    acl_config._id, rule_config.get('description'))
                continue

            has_sample = False
            for sample in acl_samples:
                if str(sample.labels.get('cookie')) != str(cookie_num):
                    continue
                if sample.labels.get('dp_name') != switch:
                    continue
                if int(sample.labels.get('in_port')) != port:
                    continue
                rule_map = rules_map.setdefault(rule_config['description'], {})
                rule_map['packet_count'] = int(sample.value)
                has_sample = True
                break

            if not has_sample:
                LOGGER.warning(
                    'No ACL metric sample available for switch, port, ACL, rule:'
                    '%s, %s, %s, %s', switch, port, acl_config._id, cookie_num)

        return {'rules': rules_map}

    def update_switch_configs(self, switch_configs):
        """Update cache of switch configs"""
        self._switch_configs = switch_configs
