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
    print("See misc/system.conf for a detailed accounting of potential options.")


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


class Configurator:
    """Manager class for system configuration."""

    def __init__(self, verbose=False, use_print=False):
        self._verbose = verbose
        self._use_print = use_print

    def _log(self, message):
        if self._verbose:
            if self._use_print:
                print(message)
            else:
                LOGGER.info(message)

    def merge_config(self, base, adding):
        """Update a dict object and follow nested objects"""
        if not adding:
            return
        for key in sorted(adding.keys()):
            value = adding[key]
            if isinstance(value, dict) and key in base:
                self.merge_config(base[key], value)
            else:
                base[key] = copy.deepcopy(value)

    def load_config(self, path, filename=None, optional=False):
        """Load a config file"""
        if not path:
            return None
        config_file = os.path.join(path, filename) if filename else path
        if not os.path.exists(config_file):
            if optional:
                LOGGER.info('Skipping missing %s', config_file)
                return {}
            raise Exception('Config file %s not found.' % config_file)

        LOGGER.info('Loading config from %s', config_file)
        return self._read_config_into({}, config_file)

    def load_and_merge(self, base, path, filename=None, optional=False):
        """Load a config file and merge with an existing base"""
        self.merge_config(base, load_config(path, filename, optional))

    def write_config(self, path, filename, config):
        """Write a config file"""
        if not path:
            return
        if not os.path.exists(path):
            os.makedirs(path)
        config_file = os.path.join(path, filename)
        LOGGER.info('Writing config to %s', config_file)
        with open(config_file, 'w') as output_stream:
            output_stream.write(json.dumps(config, indent=2, sort_keys=True))
            output_stream.write('\n')

    def _read_yaml_config(self, config, filename):
        self._log('Reading yaml config from %s' % filename)
        loaded_config = self.load_config(filename)
        if 'include' in loaded_config:
            include = loaded_config['include']
            del loaded_config['include']
            self._read_config_into(config, include)
        return self.merge_config(config, loaded_config)

    def _parse_flat_item(self, config, parts):
        key_parts = parts[0].strip().split('.', 1)
        value = parts[1].strip().strip('"').strip("'") if isinstance(parts[1], str) else parts[1]
        if len(key_parts) == 1:
            config[key_parts[0]] = value
        else:
            self._parse_flat_item(config.setdefault(key_parts[0], {}), (key_parts[1], value))

    def _read_flat_config(self, config, filename):
        self._log('Reading flat config from %s' % filename)
        with open(filename) as file:
            line = file.readline()
            while line:
                parts = re.sub(r'#.*', '', line).strip().split('=', 1)
                entry = parts[0].split() if parts else None
                if len(parts) == 2:
                    self._parse_flat_item(config, parts)
                elif len(entry) == 2 and entry[0] == 'source':
                    self._read_config_into(config, entry[1])
                elif parts and parts[0]:
                    raise Exception('Unknown config entry: %s' % line)
                line = file.readline()
        return config

    def _read_config_into(self, config, filename):
        if filename.endswith('.yaml') or filename.endswith('.json'):
            return self._read_yaml_config(config, filename)
        if filename.endswith('.conf'):
            return self._read_flat_config(config, filename)
        raise Exception('Unknown config file type: %s' % filename)

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
                    self._read_config_into(config, arg)
        return config


if __name__ == '__main__':
    CONFIG = Configurator()
    print_config(CONFIG.parse_args(sys.argv))
