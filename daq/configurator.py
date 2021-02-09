#!/usr/bin/env python3

"""Configuration manager class for daqy-things."""

import collections.abc
import copy
import json
import os
import re
import sys
import yaml
import logger

LOGGER = logger.get_logger('config')

FLAG_MAP = {
    'b': 'build_tests',
    'c': 'use_console',
    'd': 'debug_mode',
    'e': 'event_trigger',
    'f': 'fail_mode',
    'h': 'show_help',
    'k': 'keep_hold',
    'l': 'result_linger',
    'n': 'no_test',
    's': 'single_shot'
}


def show_help():
    """Show help information on the console output."""
    print("Common run options:")
    for option in FLAG_MAP:
        print("  -%s: %s" % (option, FLAG_MAP[option]))
    print("See firebase/public/protos.html#DaqConfig for all config options.")


def _append_config(config_list, prefix, config):
    for key in sorted(config.keys()):
        value = config[key]
        if isinstance(value, collections.abc.Mapping):
            new_prefix = prefix + key + '.'
            _append_config(config_list, new_prefix, value)
        else:
            quote = '"' if ' ' in str(value) else ''
            config_list.append("%s%s=%s%s%s" % (prefix, key, quote, config[key], quote))


def print_config(config):
    """Dump config info as key=value to console out."""
    config_list = []
    _append_config(config_list, '', config)
    print(*config_list, sep='\n')


def print_json(config):
    """Dump config info as json to console out."""
    print(json.dumps(config, indent=2, sort_keys=True))


class Configurator:
    """Manager class for system configuration."""

    def __init__(self, raw_print=False):
        self._raw_print = raw_print

    def _log(self, message):
        if self._raw_print:
            print(message)
        else:
            LOGGER.info(message)

    def merge_config(self, base, config_file, traversed=None):
        """Update a dict object and follow nested objects"""
        config_file = os.path.abspath(config_file)
        config = self._read_config(config_file)
        if not traversed:
            traversed = set()
        if config_file in traversed:
            raise Exception('Circular include in config file %s' % config_file)
        traversed.add(config_file)
        if 'include' in config:
            include = config.pop('include')
            including_config_file = include if include.startswith('/') else os.path.join(
                os.path.dirname(config_file), include)
            self._log('Including config file %s' % including_config_file)
            self.merge_config(base, including_config_file, traversed=traversed)
        return self._deep_merge_dict(base, config)

    def load_config(self, config_file, optional=False):
        """Load a config file"""
        if not os.path.exists(config_file):
            if optional:
                self._log('Skipping missing config file %s' % config_file)
                return {}
            raise Exception('Config file %s not found.' % config_file)
        return self.merge_config({}, config_file)

    def write_config(self, config, config_file):
        """Write a config file"""
        path = os.path.dirname(config_file)
        if not os.path.exists(path):
            os.makedirs(path)
        self._log('Writing config to %s' % config_file)
        with open(config_file, 'w') as output_stream:
            output_stream.write(json.dumps(config, indent=2, sort_keys=True))
            output_stream.write('\n')

    def _deep_merge_dict(self, base, adding):
        for key, value in adding.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                self._deep_merge_dict(base[key], value)
            else:
                base[key] = copy.deepcopy(value)
        return base

    def _read_yaml_config(self, config_file):
        # Fills in env var
        env_regex = re.compile(r'\$\{(.*)\}')

        def env_constructor(loader, node):
            match = env_regex.match(node.value)
            env_var = match.group()[2:-1]
            return os.getenv(env_var) + node.value[match.end():]

        yaml.add_implicit_resolver('!env', env_regex, None, yaml.SafeLoader)
        yaml.add_constructor('!env', env_constructor, yaml.SafeLoader)
        with open(config_file) as data_file:
            loaded_config = yaml.safe_load(data_file)
        return loaded_config

    def _parse_flat_item(self, config, parts):
        key_parts = parts[0].strip().split('.', 1)
        value = parts[1].strip().strip('"').strip("'") if isinstance(parts[1], str) else parts[1]
        if len(key_parts) == 1:
            config[key_parts[0]] = value
        else:
            self._parse_flat_item(config.setdefault(key_parts[0], {}), (key_parts[1], value))

    def _read_flat_config(self, config_file):
        loaded_config = {}
        with open(config_file) as file:
            line = file.readline()
            while line:
                parts = re.sub(r'#.*', '', line).strip().split('=', 1)
                if len(parts) == 2:
                    self._parse_flat_item(loaded_config, parts)
                elif parts and parts[0]:
                    raise Exception('Unknown config entry: %s' % line)
                line = file.readline()
        return loaded_config

    def _read_config(self, config_file):
        if config_file.endswith('.yaml') or config_file.endswith('.json'):
            return self._read_yaml_config(config_file)
        if config_file.endswith('.conf'):
            return self._read_flat_config(config_file)
        raise Exception('Unknown config file type: %s' % config_file)

    def parse_args(self, args):
        """Parse command line arguments"""
        config = {}
        for arg in args[1:]:
            if arg:
                self._log('processing arg: %s' % arg)
                if arg[0] == '-':
                    if arg[1:] in FLAG_MAP:
                        self._parse_flat_item(config, (FLAG_MAP[arg[1:]], True))
                    else:
                        raise Exception('Unknown command line arg %s' % arg)
                elif '=' in arg:
                    self._parse_flat_item(config, arg.split('=', 1))
                else:
                    config = self.merge_config(config, arg)
        return config


if __name__ == '__main__':
    CONFIG = Configurator()
    if sys.argv[1] == '--json':
        print_json(CONFIG.parse_args(sys.argv[1:]))
    else:
        print_config(CONFIG.parse_args(sys.argv))
