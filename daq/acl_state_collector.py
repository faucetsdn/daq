"""Process ACL states"""

from __future__ import absolute_import

import logger
from utils import dict_proto

from proto.acl_counts_pb2 import AclCount

LOGGER = logger.get_logger('aclstate')


class AclStateCollector:
    """Processing ACL states for ACL counting"""

    def __init__(self):
        self._switch_configs = {}

    def get_port_acl_count(self, switch, port, acl_samples):
        """Return the ACL count for a port"""

        acl_config, error_map = self._verify_port_acl_config(switch, port)

        if not acl_config:
            return dict_proto(error_map, AclCount)

        acl_count = self._get_port_acl_count(switch, port, acl_config, acl_samples)
        return dict_proto(acl_count, AclCount)

    # pylint: disable=protected-access
    def _get_port_acl_count(self, switch, port, acl_config, acl_samples):
        acl_map = {'rules': {}, 'errors': []}
        rules_map = acl_map['rules']
        errors = acl_map['errors']

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
                error = (f'No ACL metric sample available for switch, port, ACL, rule: '
                         f'{switch}, {port}, {acl_config._id}, {cookie_num}')
                errors.append(error)
                LOGGER.error(error)

        return acl_map

    def _verify_port_acl_config(self, switch, port):
        error_map = {'errors': []}
        error_list = error_map['errors']

        switch_config = self._switch_configs.get(switch)
        if not switch_config:
            error = f'Switch not defined in Faucet dps config: {switch}'
            LOGGER.error(error)
            error_list.append(error)
            return None, error_map

        port_config = switch_config.ports.get(port)
        if not port_config:
            error = f'Port not defined in Faucet dps config: {switch}, {port}'
            LOGGER.error(error)
            error_list.append(error)
            return None, error_map

        acls_config = port_config.acls_in
        if not acls_config:
            error = f'No ACLs applied to port: {switch}, {port}'
            LOGGER.error(error)
            error_list.append(error)
            return None, error_map

        return acls_config[0], None

    def update_switch_configs(self, switch_configs):
        """Update cache of switch configs"""
        self._switch_configs = switch_configs
